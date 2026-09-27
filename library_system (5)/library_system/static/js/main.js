// Cursor-reactive tilt for catalog cards — like lifting a card partway out
// of a drawer to read it, tilting toward wherever you're holding it.
function initCardTilt() {
  const cards = document.querySelectorAll('.catalog-card');
  cards.forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const cx = rect.width / 2;
      const cy = rect.height / 2;
      const ry = ((x - cx) / cx) * 4;   // rotateY
      const rx = -((y - cy) / cy) * 4;  // rotateX
      card.style.setProperty('--ry', `${ry}deg`);
      card.style.setProperty('--rx', `${rx}deg`);
    });
    card.addEventListener('mouseleave', () => {
      card.style.setProperty('--ry', `0deg`);
      card.style.setProperty('--rx', `0deg`);
    });
  });
}

// Small magnetic pull on primary buttons toward the cursor.
function initMagneticButtons() {
  const buttons = document.querySelectorAll('.btn-primary, .search-btn');
  buttons.forEach(btn => {
    btn.addEventListener('mousemove', (e) => {
      const rect = btn.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      btn.style.transform = `translate(${x * 0.12}px, ${y * 0.28 - 2}px)`;
    });
    btn.addEventListener('mouseleave', () => {
      btn.style.transform = '';
    });
  });
}

// Animates stat numbers counting up from 0 to their target value on load.
function initCountUp() {
  const nums = document.querySelectorAll('.stat-num[data-count], .stat-chip-num[data-count]');
  nums.forEach(el => {
    const target = parseInt(el.getAttribute('data-count'), 10) || 0;
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
  initMagneticButtons();
  initCountUp();
});
