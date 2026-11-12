/*
 * admin.js — small client-side helpers for the staff pages.
 *
 *  1. List filter (port of app/admin/AdminSearch.tsx): hides country rows that don't match the
 *     query and region groups that end up empty. It toggles visibility of nodes that are already
 *     in the page, and re-applies itself whenever Dash re-renders the list.
 *  2. Unsaved-changes guard (port of app/admin/country/[iso]/UnsavedGuard.tsx): warns before the
 *     tab is closed or reloaded while the country form has unsaved edits.
 */
(function () {
  "use strict";

  // ── 1. list filter ────────────────────────────────────────────────────────
  var query = "";
  var scheduled = false;

  function apply() {
    scheduled = false;
    var q = query;
    document.querySelectorAll("[data-country]").forEach(function (row) {
      var hay = row.getAttribute("data-country") || "";
      row.style.display = !q || hay.indexOf(q) !== -1 ? "" : "none";
    });
    document.querySelectorAll("[data-region-group]").forEach(function (group) {
      var any = Array.prototype.some.call(group.querySelectorAll("[data-country]"), function (r) {
        return r.style.display !== "none";
      });
      group.style.display = any ? "" : "none";
    });
  }

  function schedule() {
    if (!scheduled) {
      scheduled = true;
      window.requestAnimationFrame(apply);
    }
  }

  // Dash replaces the whole list after a contact is added / edited — keep the filter in force.
  function observe() {
    new MutationObserver(function () { if (query) schedule(); }).observe(document.body, {
      childList: true,
      subtree: true,
    });
  }
  if (document.body) observe();
  else document.addEventListener("DOMContentLoaded", observe);

  // ── 2. unsaved-changes guard ──────────────────────────────────────────────
  var dirty = false;

  function inForm(el) {
    return el && el.closest && el.closest("#country-form");
  }
  ["input", "change"].forEach(function (type) {
    document.addEventListener(type, function (e) { if (inForm(e.target)) dirty = true; }, true);
  });
  // react-select (dcc.Dropdown) does not emit native change events
  document.addEventListener("click", function (e) {
    var t = e.target;
    if (t && t.closest) {
      if (t.closest("#country-form") && t.closest(".Select-menu-outer")) dirty = true;
      if (t.closest("[data-pp-save]")) dirty = false; // any save clears the flag, like the original
    }
  }, true);
  window.addEventListener("beforeunload", function (e) {
    if (dirty && document.getElementById("country-form")) {
      e.preventDefault();
      e.returnValue = "";
    }
  });

  window.ppAdmin = {
    setFilter: function (value) {
      query = String(value || "").trim().toLowerCase();
      schedule();
    },
    clearDirty: function () { dirty = false; },
    markDirty: function () { dirty = true; },
  };
})();
