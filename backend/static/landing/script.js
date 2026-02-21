(() => {
  window.addEventListener('load', () => {
    document.body.classList.add('page-ready');
  });

  const nav = document.querySelector('[data-nav]');
  const mobile = document.querySelector('[data-mobile]');
  const menuBtn = document.querySelector('[data-menu-button]');
  const closeBtn = document.querySelector('[data-menu-close]');
  const backdropBtn = document.querySelector('[data-menu-backdrop]');
  const reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const setScrolled = () => {
    if (!nav) return;
    if (window.scrollY > 8) nav.classList.add('is-scrolled');
    else nav.classList.remove('is-scrolled');
  };

  const openMenu = () => {
    if (!mobile || !menuBtn) return;
    mobile.hidden = false;
    mobile.dataset.open = 'true';
    menuBtn.setAttribute('aria-expanded', 'true');
    document.documentElement.style.overflow = 'hidden';
  };

  const closeMenu = () => {
    if (!mobile || !menuBtn) return;
    mobile.dataset.open = 'false';
    menuBtn.setAttribute('aria-expanded', 'false');
    document.documentElement.style.overflow = '';
    window.setTimeout(() => {
      if (!mobile) return;
      mobile.hidden = true;
    }, 220);
  };

  window.addEventListener('scroll', setScrolled, { passive: true });
  window.addEventListener('load', setScrolled);

  if (menuBtn) menuBtn.addEventListener('click', openMenu);
  if (closeBtn) closeBtn.addEventListener('click', closeMenu);
  if (backdropBtn) backdropBtn.addEventListener('click', closeMenu);

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeMenu();
  });

  // Close mobile menu on link click
  if (mobile) {
    mobile.addEventListener('click', (e) => {
      const target = e.target;
      if (target && target.matches && target.matches('a')) closeMenu();
    });
  }

  // Scroll reveal
  const revealEls = Array.from(document.querySelectorAll('.reveal'));

  if (!reduceMotion && 'IntersectionObserver' in window) {
    const obs = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add('reveal--in');
            obs.unobserve(entry.target);
          }
        }
      },
      { threshold: 0.14, rootMargin: '0px 0px -10% 0px' }
    );

    for (const el of revealEls) obs.observe(el);
  } else {
    for (const el of revealEls) el.classList.add('reveal--in');
  }

  // Button ripple
  const rippleButtons = document.querySelectorAll('[data-ripple]');
  rippleButtons.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      if (reduceMotion) return;
      const rect = btn.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const ripple = document.createElement('span');
      ripple.className = 'ripple';
      ripple.style.left = `${x}px`;
      ripple.style.top = `${y}px`;
      btn.appendChild(ripple);
      window.setTimeout(() => ripple.remove(), 650);
    });
  });

  // Footer year
  const year = document.querySelector('[data-year]');
  if (year) year.textContent = String(new Date().getFullYear());
})();
