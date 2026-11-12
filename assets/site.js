/*
 * site.js — tiny site-wide helper.
 * The mobile menu is a <details> disclosure. Dash navigates without reloading the page, so the
 * header (and its open menu) would stay on screen — close it as soon as a link in it is used.
 */
(function () {
  "use strict";
  document.addEventListener("click", function (e) {
    var link = e.target && e.target.closest ? e.target.closest(".pp-mobile-menu a") : null;
    if (!link) return;
    var menu = link.closest("details");
    if (menu) menu.removeAttribute("open");
  });
})();
