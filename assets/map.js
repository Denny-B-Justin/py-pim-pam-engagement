/*
 * map.js — Leaflet choropleth of country engagement (port of app/map/MapClient.tsx).
 *
 * The Dash page (pages/map_page.py) renders <div id="pp-map"> and a dcc.Store holding the
 * payload; a clientside callback calls window.ppMap.render(payload).
 *
 * NOTE: Dash loads every file in /assets alphabetically, so this file runs BEFORE
 * vendor/leaflet/leaflet.js. Nothing below touches `L` until render() is called.
 */
(function () {
  "use strict";

  // Escape user-editable text (country name / focus note are editable via the admin pages)
  // before interpolating it into Leaflet popup / tooltip HTML.
  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function normalize(s) {
    return String(s)
      .toLowerCase()
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .replace(/&/g, "and")
      .replace(/[^a-z0-9 ]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  // ISO resolver bound to the current country list (from the database).
  function makeResolveIso(countries) {
    var validIso = {};
    var isoByName = {};
    countries.forEach(function (c) {
      validIso[c.iso3] = true;
      isoByName[normalize(c.name)] = c.iso3;
    });
    return function resolveIso(p) {
      var candidates = [
        p.ISO_A3, p.ISO3, p.iso_a3, p.adm0_a3, p.ADM0_A3, p.ISO_A3_EH,
        p["ISO3166-1-Alpha-3"], p.A3, p.sov_a3, p.SOV_A3, p.wb_a3, p.WB_A3,
        p.su_a3, p.SU_A3, p.brk_a3, p.BRK_A3,
      ];
      for (var i = 0; i < candidates.length; i++) {
        var c = candidates[i];
        if (c && typeof c === "string" && c !== "-99" && c.length === 3) {
          var up = c.toUpperCase();
          if (validIso[up]) return up;
          if (up === "KOS" && validIso["XKX"]) return "XKX";
        }
      }
      var nameCandidates = [p.ADMIN, p.NAME, p.name, p.NAME_EN, p.NAME_LONG, p.FORMAL_EN, p.sovereignt];
      for (var j = 0; j < nameCandidates.length; j++) {
        var n = nameCandidates[j];
        if (!n) continue;
        var key = normalize(String(n));
        if (isoByName[key]) return isoByName[key];
        if (key.indexOf("kosovo") !== -1 && validIso["XKX"]) return "XKX";
      }
      return null;
    };
  }

  function pickLabelAnchor(layer, resolveIso, labelOverride) {
    var f = layer.feature;
    var iso = resolveIso((f && f.properties) || {});
    if (iso && labelOverride[iso]) return L.latLng(labelOverride[iso][0], labelOverride[iso][1]);
    try {
      if (f.geometry && f.geometry.type === "Polygon") return layer.getBounds().getCenter();
      if (f.geometry && f.geometry.type === "MultiPolygon") {
        // centre of the bounding box of the largest polygon (mainland, not outlying islands)
        var best = null;
        var bestArea = 0;
        f.geometry.coordinates.forEach(function (poly) {
          var ring = poly[0];
          var minx = Infinity, miny = Infinity, maxx = -Infinity, maxy = -Infinity;
          ring.forEach(function (pt) {
            var x = pt[0], y = pt[1];
            if (x < minx) minx = x;
            if (x > maxx) maxx = x;
            if (y < miny) miny = y;
            if (y > maxy) maxy = y;
          });
          var area = (maxx - minx) * (maxy - miny);
          if (area > bestArea) {
            bestArea = area;
            best = [(miny + maxy) / 2, (minx + maxx) / 2];
          }
        });
        if (best) return L.latLng(best[0], best[1]);
      }
    } catch (e) { /* fall through */ }
    return layer.getBounds().getCenter();
  }

  function setLoaded() {
    var el = document.getElementById("pp-map-loading");
    if (el) el.style.display = "none";
  }

  function fetchGeo(urls) {
    // First URL that returns a usable response wins (bundled file first, CDN copies as fallback).
    return urls.reduce(function (chain, url) {
      return chain.catch(function () {
        return fetch(url).then(function (res) {
          if (!res.ok) throw new Error("HTTP " + res.status);
          return res.json();
        });
      });
    }, Promise.reject(new Error("start")));
  }

  function navigate(search) {
    var cs = window.dash_clientside;
    if (cs && typeof cs.set_props === "function") {
      cs.set_props("pp-url", { search: search });
      return true;
    }
    return false;
  }

  var state = { map: null, tries: 0 };

  function render(payload) {
    if (!payload || !payload.countries) return;
    var container = document.getElementById("pp-map");
    if (!container) {
      // the layout may not be in the DOM yet when the callback fires
      if (state.tries++ < 60) setTimeout(function () { render(payload); }, 50);
      return;
    }
    state.tries = 0;
    if (typeof L === "undefined") {
      if (state.tries++ < 60) setTimeout(function () { render(payload); }, 50);
      return;
    }
    if (container._leaflet_id) return; // already initialised for this element

    if (state.map) { // a previous map instance whose element was removed by navigation
      try { state.map.remove(); } catch (e) { /* ignore */ }
      state.map = null;
    }

    var cfg = payload.config;
    var colors = payload.colors;
    var darkFill = {};
    payload.darkFill.forEach(function (s) { darkFill[s] = true; });
    var smallLabel = {};
    cfg.smallLabelIso.forEach(function (i) { smallLabel[i] = true; });
    var clusterIso = {};
    cfg.clusterIso.forEach(function (i) { clusterIso[i] = true; });

    var resolveIso = makeResolveIso(payload.countries);
    var dataByIso = {};
    payload.countries.forEach(function (c) { dataByIso[c.iso3] = c; });

    var map = L.map(container, {
      worldCopyJump: true,
      minZoom: cfg.minZoom,
      maxZoom: cfg.maxZoom,
      attributionControl: true,
    }).setView(cfg.center, cfg.zoom);
    state.map = map;

    // Keyless light-gray basemap from Esri (no API key). Note the {z}/{y}/{x} tile order.
    L.tileLayer(cfg.tileUrl, { attribution: cfg.tileAttribution, maxZoom: cfg.tileMaxZoom }).addTo(map);

    var clusterLabels = [];
    var wbHint = null;

    function updateClusterLabels() {
      var reveal = map.getZoom() >= cfg.clusterLabelMinZoom;
      clusterLabels.forEach(function (o) {
        var on = map.hasLayer(o.lbl);
        if (reveal && !on) o.lbl.addTo(map);
        else if (!reveal && on) map.removeLayer(o.lbl);
      });
      if (!clusterLabels.length) return;
      if (!reveal) {
        if (!wbHint) {
          wbHint = L.marker(cfg.clusterHintLatLng, {
            interactive: false,
            keyboard: false,
            icon: L.divIcon({
              className: "wb-hint",
              html: cfg.clusterHintHtml,
              iconSize: [160, 34],
              iconAnchor: [80, 17],
            }),
          }).addTo(map);
        }
      } else if (wbHint) {
        map.removeLayer(wbHint);
        wbHint = null;
      }
    }

    // In-app navigation from a popup link (no full page reload; falls back to a normal link).
    container.addEventListener("click", function (ev) {
      var a = ev.target.closest ? ev.target.closest("a[data-pp-search]") : null;
      if (!a || ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.button === 1) return;
      if (navigate(a.getAttribute("data-pp-search"))) ev.preventDefault();
    });

    var layer = null;
    function build(geo) {
      layer = L.geoJSON(geo, {
        style: function (feature) {
          var d = feature ? dataByIso[resolveIso(feature.properties || {}) || ""] : null;
          if (!d) return { fillColor: "#e8edf2", color: "#c5cdd6", weight: 0.35, fillOpacity: 0.55 };
          return { fillColor: colors[d.status], color: "#fff", weight: 1.1, fillOpacity: 0.95 };
        },
        onEachFeature: function (feature, lyr) {
          var iso = resolveIso(feature.properties || {});
          var d = iso ? dataByIso[iso] : null;
          if (!d || !iso) { lyr.options.interactive = false; return; }

          lyr.bindTooltip(esc(d.name) + " — " + esc(d.status), {
            className: "country-tip",
            sticky: true,
            direction: "auto",
          });

          var pill = d.status === "Inception"
            ? "background:" + colors[d.status] + ";color:#5a4500;"
            : "background:" + colors[d.status] + ";color:white;";
          var href = payload.detailHref.replace("__ISO__", encodeURIComponent(iso));
          var search = "?" + href.split("?")[1];
          lyr.bindPopup(
            '<div style="font-family:inherit;min-width:240px">' +
              '<h3 style="margin:0 0 4px 0;font-size:14px;color:#1F4E79">' + esc(d.name) + "</h3>" +
              '<span style="display:inline-block;padding:2px 8px;border-radius:11px;font-size:11px;font-weight:600;' + pill + '">' + esc(d.status) + "</span>" +
              '<div style="font-size:11.5px;color:#5a6470;margin:4px 0"><b>Region:</b> ' + esc(d.region) + "</div>" +
              '<div style="font-size:11.5px;color:#1f2d3d;line-height:1.4;margin-top:6px;padding-top:6px;border-top:1px solid #eee">' + esc(d.focus) + "</div>" +
              '<a href="' + esc(href) + '" data-pp-search="' + esc(search) + '" style="display:inline-block;margin-top:8px;font-size:12px;color:#1F4E79;font-weight:600">' + esc(cfg.popupLinkLabel) + "</a>" +
            "</div>"
          );

          lyr.on({
            mouseover: function (e) { e.target.setStyle({ weight: 2.4, color: "#0c2a47", fillOpacity: 1 }); },
            mouseout: function (e) { layer.resetStyle(e.target); },
          });

          var center = pickLabelAnchor(lyr, resolveIso, cfg.labelOverride);
          var classes = ["country-name-label", darkFill[d.status] ? "on-dark" : "", smallLabel[iso] ? "small" : ""]
            .filter(Boolean)
            .join(" ");
          var lbl = L.tooltip({
            permanent: true,
            direction: "center",
            className: classes,
            interactive: false,
            opacity: 1,
          }).setLatLng(center).setContent(esc(d.name));

          if (clusterIso[iso]) {
            clusterLabels.push({ lbl: lbl, iso: iso });
            if (map.getZoom() >= cfg.clusterLabelMinZoom) lbl.addTo(map);
          } else {
            lbl.addTo(map);
          }
        },
      }).addTo(map);
      updateClusterLabels();
      map.on("zoomend", updateClusterLabels);
      setLoaded();
    }

    fetchGeo([payload.geojsonUrl].concat(cfg.geojsonFallbackUrls || []))
      .then(build)
      .catch(function () { setLoaded(); }); // every source failed — clear the overlay so the panel isn't stuck
  }

  window.ppMap = { render: render };
})();
