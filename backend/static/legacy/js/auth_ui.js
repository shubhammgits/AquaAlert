(function () {
  "use strict";

  function setEyeIcon(button, isVisible) {
    button.setAttribute("aria-pressed", String(isVisible));
    button.innerHTML = isVisible
      ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" stroke="currentColor" stroke-width="2"/><path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" stroke="currentColor" stroke-width="2"/></svg>'
      : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" stroke="currentColor" stroke-width="2"/><path d="M4 4l16 16" stroke="currentColor" stroke-width="2"/><path d="M10.6 10.6a3 3 0 0 0 4.24 4.24" stroke="currentColor" stroke-width="2"/></svg>';
  }

  function bindPasswordToggle(button) {
    var inputId = button.getAttribute("aria-controls");
    if (!inputId) return;
    var input = document.getElementById(inputId);
    if (!input) return;

    setEyeIcon(button, input.type === "text");

    button.addEventListener("click", function () {
      var isVisible = input.type === "password";
      input.type = isVisible ? "text" : "password";
      setEyeIcon(button, isVisible);
      input.focus();
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var toggles = document.querySelectorAll("[data-toggle-password]");
    toggles.forEach(bindPasswordToggle);
  });
})();
