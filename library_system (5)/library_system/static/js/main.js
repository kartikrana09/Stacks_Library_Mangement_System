function initCardTilt() {
  if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches ||
      window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const cards = document.querySelectorAll('.catalog-card');
  cards.forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const cx = rect.width / 2 || 1;
      const cy = rect.height / 2 || 1;
      const ry = ((x - cx) / cx) * 2;
      const rx = -((y - cy) / cy) * 2;
      card.style.setProperty('--ry', `${ry}deg`);
      card.style.setProperty('--rx', `${rx}deg`);
    });
    card.addEventListener('mouseleave', () => {
      card.style.setProperty('--ry', `0deg`);
      card.style.setProperty('--rx', `0deg`);
    });
  });
}

function initBookIntro() {
  const intro = document.querySelector('.book-intro');
  if (!intro || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  let framePending = false;
  const updateProgress = () => {
    const introTop = intro.getBoundingClientRect().top + window.scrollY;
    const scrollDistance = Math.max(1, intro.offsetHeight - window.innerHeight);
    const rawProgress = Math.min(1, Math.max(0, (window.scrollY - introTop) / scrollDistance));
    const progress = rawProgress * rawProgress * (3 - 2 * rawProgress);
    const pageTurn = (start, end) => Math.min(1, Math.max(0, (progress - start) / (end - start)));
    intro.style.setProperty('--intro-progress', progress.toFixed(3));
    intro.style.setProperty('--page-one-progress', pageTurn(.12, .48).toFixed(3));
    intro.style.setProperty('--page-two-progress', pageTurn(.32, .68).toFixed(3));
    intro.style.setProperty('--page-three-progress', pageTurn(.54, .88).toFixed(3));
    framePending = false;
  };
  const scheduleUpdate = () => {
    if (!framePending) {
      framePending = true;
      window.requestAnimationFrame(updateProgress);
    }
  };

  window.addEventListener('scroll', scheduleUpdate, { passive: true });
  window.addEventListener('resize', scheduleUpdate);
  updateProgress();
}

function initCatalogReveal() {
  const catalog = document.querySelector('.catalog-app');
  if (!catalog || window.matchMedia('(prefers-reduced-motion: reduce)').matches ||
      !('IntersectionObserver' in window)) return;

  catalog.classList.add('catalog-reveal');
  const observer = new IntersectionObserver(entries => {
    if (entries.some(entry => entry.isIntersecting)) {
      catalog.classList.add('is-visible');
      observer.disconnect();
    }
  }, { threshold: 0.06 });
  observer.observe(catalog);
}

function initSidebarToggle() {
  const toggle = document.querySelector('.sidebar-toggle');
  if (!toggle) return;

  toggle.addEventListener('click', () => {
    const collapsed = document.body.classList.toggle('sidebar-collapsed');
    toggle.setAttribute('aria-expanded', String(!collapsed));
  });
}

function initCountUp() {
  const nums = document.querySelectorAll('.stat-num[data-count], .stat-chip-num[data-count]');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  nums.forEach(el => {
    const target = parseInt(el.getAttribute('data-count'), 10) || 0;
    if (reducedMotion) {
      el.textContent = target;
      return;
    }
    const duration = 700;
    const start = performance.now();
    function tick(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(eased * target);
      if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initCardTilt();
  initBookIntro();
  initCatalogReveal();
  initSidebarToggle();
  initCountUp();
});
