(function () {
  function markReady() {
    try {
      const b = document.body;
      if (!b) return;
      if (!b.classList.contains("portal")) return;
      requestAnimationFrame(() => b.classList.add("portal-ready"));
    } catch {
      // ignore
    }
  }

  function initSectionReveal() {
    try {
      const b = document.body;
      if (!b || !b.classList.contains("portal")) return;
      if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

      const targets = Array.from(document.querySelectorAll(".portal .card, .portal .sidepanel"));
      if (!targets.length) return;

      // Mark targets as reveal-able (CSS handles initial hidden state).
      targets.forEach((el) => el.classList.add("reveal"));

      if (!("IntersectionObserver" in window)) {
        targets.forEach((el) => el.classList.add("is-visible"));
        return;
      }

      const io = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add("is-visible");
              io.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.12, rootMargin: "0px 0px -10% 0px" }
      );

      targets.forEach((el) => io.observe(el));
    } catch {
      // ignore
    }
  }

  function toggleGroup(button) {
    const targetId = button.getAttribute("data-nav-toggle");
    if (!targetId) return;

    const group = document.getElementById(targetId);
    if (!group) return;

    const expanded = button.getAttribute("aria-expanded") === "true";
    button.setAttribute("aria-expanded", expanded ? "false" : "true");
    group.classList.toggle("is-open", !expanded);
  }

  document.addEventListener("click", (e) => {
    const btn = e.target && e.target.closest ? e.target.closest("[data-nav-toggle]") : null;
    if (!btn) return;
    e.preventDefault();
    toggleGroup(btn);
  });

  // Auto-open group if URL hash matches a sub-link
  function openIfHashMatches() {
    const hash = (window.location.hash || "").trim();
    if (!hash || hash.length < 2) return;

    const link = document.querySelector(`.nav__group a[href='${hash}']`);
    if (!link) return;

    const group = link.closest(".nav__group");
    if (!group || !group.id) return;

    const btn = document.querySelector(`[data-nav-toggle='${group.id}']`);
    if (!btn) return;

    btn.setAttribute("aria-expanded", "true");
    group.classList.add("is-open");
  }

  window.addEventListener("hashchange", openIfHashMatches);
  openIfHashMatches();

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      markReady();
      initSectionReveal();
    });
  } else {
    markReady();
    initSectionReveal();
  }
})();
