#!/usr/bin/env python3
"""
load_csv_to_uc.py — load the Supabase export (CSV or Excel) into the Unity Catalog tables.

Run it from anywhere; it finds the project root itself and uses the same settings as the app
(constants.py + the .env file / environment variables), so no credentials live in this file.

    # 1. check the export without touching Databricks (no credentials needed)
    python migration/load_csv_to_uc.py --dir ./export --dry-run

    # 2. load it (the tables must already exist: run 01_create_tables.sql first)
    python migration/load_csv_to_uc.py --dir ./export

    # one workbook with a sheet per table works too, and the two can be mixed
    python migration/load_csv_to_uc.py --xlsx supabase_export.xlsx

What it expects
    One file (or sheet) per Supabase table, named after the table:
        countries.csv  country_contacts.csv  pim_counterparts.csv  assessments.csv
        projects.csv   events.csv            deleted_records.csv   epim_cba_projects.csv (optional)
    The first row holds the column names. Files named after the Unity Catalog table
    (e.g. pimpam_countries.csv) are accepted as well.

What it does
    * converts every value to the column's Unity Catalog type (Postgres `t`/`f` booleans,
      `2026-06-10 12:00:00+00` timestamps, numeric ids -> STRING, Excel dates, ...);
    * rewrites deleted_records.table_name from the Supabase name to the Unity Catalog name;
    * validates EVERYTHING first and writes nothing if a single value is bad;
    * refuses to load into a table that already has rows unless you pass --truncate;
    * inserts in small batches with bound parameters, then compares row counts.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import constants as C  # noqa: E402
from services import db  # noqa: E402
from services import repository as repo  # noqa: E402

csv.field_size_limit(50_000_000)

MAX_ERRORS_SHOWN = 30
_TRUE = {"t", "true", "1", "yes", "y"}
_FALSE = {"f", "false", "0", "no", "n"}


# ═════════════════════════════════════════════════════════════════════════════
# reading the export
# ═════════════════════════════════════════════════════════════════════════════
class Source:
    """Finds the rows of a Supabase table in a folder of CSV files and / or an Excel workbook."""

    def __init__(self, directory: Path | None, workbook: Path | None):
        self.directory = directory
        self.workbook = workbook
        self._wb = None
        if workbook is not None:
            from openpyxl import load_workbook

            self._wb = load_workbook(workbook, read_only=True, data_only=True)

    def read(self, supabase_name: str, uc_name: str) -> tuple[str, list[dict[str, Any]]] | None:
        """Return (where-it-came-from, rows) or None when the table is not in the export."""
        names = (supabase_name, uc_name)
        if self.directory is not None:
            by_lower = {p.name.lower(): p for p in self.directory.glob("*.csv")}
            for n in names:
                path = by_lower.get(f"{n}.csv".lower())
                if path:
                    return path.name, self._read_csv(path)
        if self._wb is not None:
            sheets = {s.lower(): s for s in self._wb.sheetnames}
            for n in names:
                if n.lower() in sheets:
                    return f"{self.workbook.name}[{sheets[n.lower()]}]", self._read_sheet(self._wb[sheets[n.lower()]])
        return None

    @staticmethod
    def _read_csv(path: Path) -> list[dict[str, Any]]:
        with path.open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            if header is None:
                return []
            cols = [h.strip().lower() for h in header]
            rows = []
            for rec in reader:
                if not any((v or "").strip() for v in rec):
                    continue
                rows.append(dict(zip(cols, rec)))
            return rows

    @staticmethod
    def _read_sheet(ws) -> list[dict[str, Any]]:
        it = ws.iter_rows(values_only=True)
        header = next(it, None)
        if header is None:
            return []
        cols = [str(h).strip().lower() if h is not None else "" for h in header]
        rows = []
        for rec in it:
            if not any(v is not None and str(v).strip() for v in rec):
                continue
            rows.append({c: v for c, v in zip(cols, rec) if c})
        return rows


# ═════════════════════════════════════════════════════════════════════════════
# value conversion
# ═════════════════════════════════════════════════════════════════════════════
def _blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def convert(typ: str, value: Any) -> Any:
    """Convert one cell to the Python value for a Unity Catalog column type. Raises ValueError."""
    if _blank(value):
        return None
    if typ == "STRING":
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, float) and value.is_integer():  # Excel stores 12 as 12.0
            return str(int(value))
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return str(value).strip()
    if typ == "BOOLEAN":
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in _TRUE:
            return True
        if text in _FALSE:
            return False
        raise ValueError(f"{value!r} is not a boolean (use true/false, t/f, 1/0)")
    if typ == "INT":
        number = float(str(value).strip())
        if not number.is_integer():
            raise ValueError(f"{value!r} is not a whole number")
        return int(number)
    if typ == "DOUBLE":
        return float(str(value).strip())
    if typ == "DATE":
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        parsed = repo.parse_day(value)
        if parsed is None:
            raise ValueError(f"{value!r} is not a date (expected YYYY-MM-DD)")
        return parsed
    if typ == "TIMESTAMP":
        if isinstance(value, date) and not isinstance(value, datetime):
            value = datetime(value.year, value.month, value.day)
        parsed = repo.parse_ts(value)
        if parsed is None:
            raise ValueError(f"{value!r} is not a timestamp")
        return parsed.astimezone(timezone.utc)
    raise ValueError(f"unsupported column type {typ}")  # pragma: no cover


def _clean_id(value: Any) -> str | None:
    text = convert("STRING", value)
    return text or None


def _columns(uc_table: str) -> dict[str, str]:
    return C.COUNTRY_COLUMNS if uc_table == C.TBL_COUNTRIES else C.CHILD_TABLE_COLUMNS[uc_table]


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def prepare(supabase_name: str, uc_table: str, origin: str, raw_rows: list[dict[str, Any]], rep: Report) -> list[dict[str, Any]]:
    """Validate + convert every row of one table. Problems go to `rep`; the good rows are returned."""
    types = _columns(uc_table)
    present = set(raw_rows[0]) if raw_rows else set()
    unknown = sorted(present - set(types))
    if unknown:
        rep.warn(f"{origin}: ignoring columns that do not exist in {uc_table}: {', '.join(unknown)}")
    missing = sorted(set(types) - present - ({"id"} if uc_table != C.TBL_COUNTRIES else set()))
    if raw_rows and missing:
        rep.warn(f"{origin}: no data for {uc_table} columns (they will be NULL): {', '.join(missing)}")

    out: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    generated_ids = 0
    for n, raw in enumerate(raw_rows, start=2):  # row 1 is the header
        where = f"{origin} row {n}"
        row: dict[str, Any] = {}
        ok = True
        for col, typ in types.items():
            try:
                row[col] = convert(typ, raw.get(col))
            except (ValueError, TypeError) as exc:
                rep.error(f"{where}, column '{col}': {exc}")
                ok = False
        if not ok:
            continue

        if not row.get("iso3"):
            rep.error(f"{where}: iso3 is empty")
            continue
        row["iso3"] = row["iso3"].upper()

        if uc_table == C.TBL_COUNTRIES:
            key = row["iso3"]
            if len(key) != 3:
                rep.error(f"{where}: iso3 {key!r} is not a 3-letter code")
                continue
        else:
            rid = _clean_id(raw.get("id"))
            if rid is None:
                rid = str(uuid.uuid4())
                generated_ids += 1
            row["id"] = key = rid
        if key in seen_keys:
            rep.error(f"{where}: duplicate {'iso3' if uc_table == C.TBL_COUNTRIES else 'id'} {key!r}")
            continue
        seen_keys.add(key)

        if uc_table == C.TBL_DELETED:
            if not _fix_deleted_row(row, where, rep):
                continue
        out.append(row)

    if generated_ids:
        rep.warn(f"{origin}: {generated_ids} row(s) had no id — new UUIDs were generated")
    return out


def _fix_deleted_row(row: dict[str, Any], where: str, rep: Report) -> bool:
    """deleted_records: Supabase table name -> Unity Catalog name; payload must be valid JSON."""
    name = row.get("table_name") or ""
    mapped = C.SUPABASE_TO_UC_TABLES.get(name, name if name in C.CHILD_TABLE_COLUMNS else None)
    if mapped is None or mapped == C.TBL_COUNTRIES:
        rep.error(f"{where}: table_name {name!r} is not a child table of this app")
        return False
    row["table_name"] = mapped
    payload = row.get("payload")
    if payload is None:
        rep.error(f"{where}: payload is empty")
        return False
    try:
        row["payload"] = json.dumps(json.loads(payload), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        rep.error(f"{where}: payload is not valid JSON ({exc})")
        return False
    if row.get("deleted_at") is None:
        row["deleted_at"] = datetime.now(timezone.utc)
    return True


# ═════════════════════════════════════════════════════════════════════════════
# writing
# ═════════════════════════════════════════════════════════════════════════════
def _marker(types: dict[str, str], col: str, key: str) -> str:
    # Python ints are bound as BIGINT; the INT columns need an explicit cast.
    return f"CAST(:{key} AS INT)" if types[col] == "INT" else f":{key}"


def insert_batch(uc_table: str, rows: list[dict[str, Any]]) -> None:
    types = _columns(uc_table)
    cols = list(types)
    params: dict[str, Any] = {}
    tuples = []
    for i, row in enumerate(rows):
        marks = []
        for col in cols:
            key = f"p{i}_{col}"
            params[key] = row.get(col)
            marks.append(_marker(types, col, key))
        tuples.append("(" + ", ".join(marks) + ")")
    db.execute(
        f"INSERT INTO {db.fq(uc_table)} ({', '.join(db.column(uc_table, c) for c in cols)}) VALUES " + ", ".join(tuples),
        params,
    )


def count_rows(uc_table: str) -> int:
    row = db.query_one(f"SELECT COUNT(*) AS n FROM {db.fq(uc_table)}")
    return int(row["n"]) if row else 0


def confirm(prompt: str, assume_yes: bool) -> bool:
    if assume_yes:
        return True
    if not sys.stdin.isatty():
        print(f"{prompt}\n  Not an interactive terminal — add --yes to confirm.", file=sys.stderr)
        return False
    return input(f"{prompt} Type 'yes' to continue: ").strip().lower() == "yes"


# ═════════════════════════════════════════════════════════════════════════════
# main
# ═════════════════════════════════════════════════════════════════════════════
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Load the Supabase export (CSV / Excel) into the Unity Catalog tables.")
    ap.add_argument("--dir", type=Path, help="folder with one <table>.csv per Supabase table")
    ap.add_argument("--xlsx", type=Path, help="Excel workbook with one sheet per Supabase table")
    ap.add_argument("--only", help="comma-separated Supabase table names to load (default: all that are present)")
    ap.add_argument("--dry-run", action="store_true", help="validate the export and show counts; do not connect or write")
    ap.add_argument("--truncate", action="store_true", help="empty the target tables first (DELETE FROM) instead of refusing")
    ap.add_argument("--yes", action="store_true", help="do not ask for confirmation (needed for --truncate in scripts)")
    ap.add_argument("--batch-size", type=int, default=25, help="rows per INSERT statement (default 25)")
    args = ap.parse_args(argv)

    if not args.dir and not args.xlsx:
        ap.error("give --dir (CSV files) and/or --xlsx (workbook)")
    if args.dir and not args.dir.is_dir():
        ap.error(f"{args.dir} is not a folder")
    if args.xlsx and not args.xlsx.is_file():
        ap.error(f"{args.xlsx} not found")
    if args.batch_size < 1:
        ap.error("--batch-size must be at least 1")

    wanted = [n.strip() for n in args.only.split(",") if n.strip()] if args.only else list(C.SUPABASE_TO_UC_TABLES)
    bad = [n for n in wanted if n not in C.SUPABASE_TO_UC_TABLES]
    if bad:
        ap.error(f"unknown table(s): {', '.join(bad)} — valid: {', '.join(C.SUPABASE_TO_UC_TABLES)}")

    source = Source(args.dir, args.xlsx)
    rep = Report()

    # ── 1. read + validate (nothing is written yet) ─────────────────────────
    print(f"Target: {C.CATALOG}.{C.SCHEMA}")
    prepared: dict[str, list[dict[str, Any]]] = {}
    for name in C.SUPABASE_TO_UC_TABLES:  # keep the dependency order: countries first
        if name not in wanted:
            continue
        uc = C.SUPABASE_TO_UC_TABLES[name]
        found = source.read(name, uc)
        if found is None:
            print(f"  {name:<20} (not in the export — skipped)")
            continue
        origin, raw = found
        rows = prepare(name, uc, origin, raw, rep)
        prepared[name] = rows
        print(f"  {name:<20} {len(raw):>6} rows read from {origin} -> {uc}")

    if not prepared:
        print("Nothing to load: none of the expected files / sheets were found.", file=sys.stderr)
        return 2

    # children whose country is unknown would be invisible in the app
    if "countries" in prepared:
        known = {r["iso3"] for r in prepared.get("countries", [])}
    elif args.dry_run:
        known = None
        rep.warn("countries.csv is not part of this run — country references were not checked")
    else:
        known = {r["iso3"] for r in db.query(f"SELECT iso3 FROM {db.fq(C.TBL_COUNTRIES)}")}
    if known is not None:
        for name, rows in prepared.items():
            if name == "countries":
                continue
            orphans = sorted({r["iso3"] for r in rows if r["iso3"] not in known})
            if orphans:
                rep.warn(f"{name}: iso3 not found in countries (these rows will not show in the app): {', '.join(orphans[:15])}")

    for w in rep.warnings:
        print(f"  warning: {w}")
    if rep.errors:
        print(f"\n{len(rep.errors)} problem(s) found — nothing was written:", file=sys.stderr)
        for e in rep.errors[:MAX_ERRORS_SHOWN]:
            print(f"  - {e}", file=sys.stderr)
        if len(rep.errors) > MAX_ERRORS_SHOWN:
            print(f"  ... and {len(rep.errors) - MAX_ERRORS_SHOWN} more", file=sys.stderr)
        return 2

    total = sum(len(r) for r in prepared.values())
    if args.dry_run:
        print(f"\nDry run OK: {total} rows in {len(prepared)} table(s) are ready to load. Nothing was written.")
        return 0

    # ── 2. pre-flight on the target ─────────────────────────────────────────
    if not db.is_configured():
        print("Databricks is not configured: set DATABRICKS_SERVER_HOSTNAME, DATABRICKS_HTTP_PATH, "
              "DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET (see .env.sample).", file=sys.stderr)
        return 2
    existing = {n: count_rows(C.SUPABASE_TO_UC_TABLES[n]) for n in prepared}
    filled = {n: c for n, c in existing.items() if c}
    if filled and not args.truncate:
        print("\nThese target tables already contain rows — refusing to load on top of them:", file=sys.stderr)
        for n, c in filled.items():
            print(f"  - {C.SUPABASE_TO_UC_TABLES[n]}: {c} rows", file=sys.stderr)
        print("Re-run with --truncate to replace their contents.", file=sys.stderr)
        return 2
    if filled and not confirm(f"\n--truncate will DELETE all rows from {len(filled)} table(s) in {C.CATALOG}.{C.SCHEMA}.", args.yes):
        print("Aborted.", file=sys.stderr)
        return 1

    # ── 3. load ─────────────────────────────────────────────────────────────
    print("\nLoading ...")
    for name, rows in prepared.items():
        uc = C.SUPABASE_TO_UC_TABLES[name]
        if existing[name]:
            db.execute(f"DELETE FROM {db.fq(uc)}")
        for start in range(0, len(rows), args.batch_size):
            insert_batch(uc, rows[start : start + args.batch_size])
        print(f"  {uc:<28} {len(rows):>6} rows inserted")

    # ── 4. verify ───────────────────────────────────────────────────────────
    print("\nVerifying row counts ...")
    failed = False
    for name, rows in prepared.items():
        uc = C.SUPABASE_TO_UC_TABLES[name]
        n = count_rows(uc)
        flag = "ok" if n == len(rows) else "MISMATCH"
        failed |= n != len(rows)
        print(f"  {uc:<28} expected {len(rows):>6}  found {n:>6}  {flag}")
    if failed:
        print("\nRow counts differ — check the table contents before using the app.", file=sys.stderr)
        return 3
    print(f"\nDone: {total} rows loaded. Next: start the app and open /?page=admin-dashboard to eyeball the totals.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
