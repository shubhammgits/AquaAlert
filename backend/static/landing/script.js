(() => {
  'use strict';
  
  // Wait for DOM content loaded
  const ready = (fn) => {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  };

  // Page load animation
  window.addEventListener('load', () => {
    document.body.classList.add('page-ready');
  });

  // Check for reduced motion preference
  const reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Elements
  const nav = document.querySelector('[data-nav]');
  const mobile = document.querySelector('[data-mobile]');
  const menuBtn = document.querySelector('[data-menu-button]');
  const closeBtn = document.querySelector('[data-menu-close]');
  const backdropBtn = document.querySelector('[data-menu-backdrop]');

  // Scroll progress indicator
  const createScrollProgress = () => {
    if (reduceMotion) return;
    const progress = document.createElement('div');
    progress.className = 'scroll-progress';
    document.body.appendChild(progress);
    
    const updateProgress = () => {
      const scrollTop = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const scrollPercent = docHeight > 0 ? scrollTop / docHeight : 0;
      progress.style.transform = `scaleX(${scrollPercent})`;
    };
    
    window.addEventListener('scroll', updateProgress, { passive: true });
    updateProgress();
  };

  // Navbar scroll state
  const setScrolled = () => {
    if (!nav) return;
    if (window.scrollY > 8) nav.classList.add('is-scrolled');
    else nav.classList.remove('is-scrolled');
  };

  // Mobile menu handlers
  const openMenu = () => {
    if (!mobile || !menuBtn) return;
    mobile.hidden = false;
    requestAnimationFrame(() => {
      mobile.dataset.open = 'true';
      menuBtn.setAttribute('aria-expanded', 'true');
      document.documentElement.style.overflow = 'hidden';
    });
  };

  const closeMenu = () => {
    if (!mobile || !menuBtn) return;
    mobile.dataset.open = 'false';
    menuBtn.setAttribute('aria-expanded', 'false');
    document.documentElement.style.overflow = '';
    setTimeout(() => {
      if (!mobile) return;
      mobile.hidden = true;
    }, 320);
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

  // Enhanced scroll reveal with stagger
  const initScrollReveal = () => {
    const revealEls = Array.from(document.querySelectorAll('.reveal'));

    if (reduceMotion || !('IntersectionObserver' in window)) {
      for (const el of revealEls) el.classList.add('reveal--in');
      return;
    }

    const obs = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            // Add slight random delay for organic feel
            const delay = parseInt(entry.target.style.getPropertyValue('--d') || 0);
            setTimeout(() => {
              entry.target.classList.add('reveal--in');
            }, delay);
            obs.unobserve(entry.target);
          }
        }
      },
      { threshold: 0.1, rootMargin: '0px 0px -8% 0px' }
    );

    for (const el of revealEls) obs.observe(el);
  };

  // Enhanced button ripple effect
  const initRippleEffect = () => {
    if (reduceMotion) return;
    
    const rippleButtons = document.querySelectorAll('[data-ripple]');
    rippleButtons.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const rect = btn.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const ripple = document.createElement('span');
        ripple.className = 'ripple';
        ripple.style.left = `${x}px`;
        ripple.style.top = `${y}px`;
        btn.appendChild(ripple);
        setTimeout(() => ripple.remove(), 700);
      });
    });
  };

  // Magnetic button effect (subtle)
  const initMagneticButtons = () => {
    if (reduceMotion) return;
    
    const magneticBtns = document.querySelectorAll('.btn--primary, .portal');
    
    magneticBtns.forEach((btn) => {
      btn.addEventListener('mousemove', (e) => {
        const rect = btn.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        
        const moveX = x * 0.1;
        const moveY = y * 0.1;
        
        btn.style.transform = `translate(${moveX}px, ${moveY}px) translateY(-3px) scale(1.02)`;
      });
      
      btn.addEventListener('mouseleave', () => {
        btn.style.transform = '';
      });
    });
  };

  // Parallax effect for floating cards
  const initParallax = () => {
    if (reduceMotion) return;
    
    const floatCards = document.querySelectorAll('.float');
    
    const handleScroll = () => {
      const scrollY = window.scrollY;
      floatCards.forEach((card, i) => {
        const speed = 0.05 + (i * 0.02);
        const yPos = scrollY * speed;
        card.style.transform = `translateY(${-yPos}px)`;
      });
    };
    
    // Only apply in viewport
    const heroSection = document.querySelector('.hero');
    if (heroSection) {
      const obs = new IntersectionObserver(
        (entries) => {
          if (entries[0].isIntersecting) {
            window.addEventListener('scroll', handleScroll, { passive: true });
          } else {
            window.removeEventListener('scroll', handleScroll);
            floatCards.forEach(card => card.style.transform = '');
          }
        },
        { threshold: 0 }
      );
      obs.observe(heroSection);
    }
  };

  // Smooth anchor scroll with offset
  const initSmoothScroll = () => {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function (e) {
        const targetId = this.getAttribute('href');
        if (targetId === '#') return;
        
        const target = document.querySelector(targetId);
        if (!target) return;
        
        e.preventDefault();
        
        const offset = 96; // Nav height
        const targetPosition = target.getBoundingClientRect().top + window.scrollY - offset;
        
        window.scrollTo({
          top: targetPosition,
          behavior: reduceMotion ? 'auto' : 'smooth'
        });
        
        // Update URL without triggering scroll
        history.pushState(null, '', targetId);
      });
    });
  };

  // Tilt effect for cards
  const initTiltEffect = () => {
    if (reduceMotion) return;
    
    const tiltCards = document.querySelectorAll('.float .card');
    
    tiltCards.forEach(card => {
      const parent = card.closest('.float');
      if (!parent) return;
      
      parent.addEventListener('mousemove', (e) => {
        const rect = parent.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = (y - centerY) / 20;
        const rotateY = (centerX - x) / 20;
        
        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)`;
      });
      
      parent.addEventListener('mouseleave', () => {
        card.style.transform = '';
      });
    });
  };

  // Counter animation for stats (if any)
  const initCounters = () => {
    if (reduceMotion) return;
    
    const counters = document.querySelectorAll('[data-count]');
    if (!counters.length) return;
    
    const animateCount = (el) => {
      const target = parseInt(el.dataset.count);
      const duration = 2000;
      const start = performance.now();
      
      const update = (now) => {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.floor(target * eased);
        
        if (progress < 1) {
          requestAnimationFrame(update);
        }
      };
      
      requestAnimationFrame(update);
    };
    
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            animateCount(entry.target);
            obs.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.5 }
    );
    
    counters.forEach(counter => obs.observe(counter));
  };

  // Typing effect for hero title (subtle)
  const initTypingEffect = () => {
    if (reduceMotion) return;
    
    const heroTitle = document.querySelector('.hero__title');
    if (!heroTitle || heroTitle.dataset.animated) return;
    
    heroTitle.dataset.animated = 'true';
    heroTitle.style.opacity = '1';
  };

  // Footer year
  const year = document.querySelector('[data-year]');
  if (year) year.textContent = String(new Date().getFullYear());

  // Initialize all effects
  ready(() => {
    createScrollProgress();
    initScrollReveal();
    initRippleEffect();
    initSmoothScroll();
    initTypingEffect();
    initCounters();
    
    // Delay heavy effects slightly
    setTimeout(() => {
      initMagneticButtons();
      initParallax();
      initTiltEffect();
    }, 100);
  });
})();
