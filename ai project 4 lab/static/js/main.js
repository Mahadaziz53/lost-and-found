/**
 * AI Lost & Found Intelligence System
 * main.js – Frontend Logic
 */

/* ── Sidebar Toggle ──────────────────────── */
const sidebar      = document.getElementById('sidebar');
const mainContent  = document.getElementById('mainContent');
const toggleBtn    = document.getElementById('sidebarToggle');

function isMobile() { return window.innerWidth <= 768; }

if (toggleBtn) {
  toggleBtn.addEventListener('click', () => {
    if (isMobile()) {
      sidebar.classList.toggle('open');
    } else {
      sidebar.classList.toggle('collapsed');
      mainContent.classList.toggle('expanded');
    }
  });
}

// Close sidebar on mobile when clicking outside
document.addEventListener('click', (e) => {
  if (isMobile() && sidebar && sidebar.classList.contains('open')) {
    if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
      sidebar.classList.remove('open');
    }
  }
});

/* ── Live Clock ──────────────────────────── */
const timeEl = document.getElementById('navbarTime');
function updateClock() {
  if (!timeEl) return;
  const now = new Date();
  timeEl.textContent = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
updateClock();
setInterval(updateClock, 1000);

/* ── Animated Counters ───────────────────── */
function animateCounter(el) {
  const target = parseInt(el.dataset.target, 10);
  if (isNaN(target)) return;
  const duration = 1200;
  const step     = 16;
  const steps    = duration / step;
  const inc      = target / steps;
  let current    = 0;
  const timer = setInterval(() => {
    current += inc;
    if (current >= target) { current = target; clearInterval(timer); }
    el.textContent = Math.floor(current);
  }, step);
}
document.querySelectorAll('.stat-number[data-target]').forEach(animateCounter);

/* ── File Upload Preview & Drag-and-Drop ──── */
function setupFormPage(descId, countId, areaId, inputId, previewId, previewImgId, removeId, formId) {
  // Character counter
  const desc  = document.getElementById(descId);
  const count = document.getElementById(countId);
  if (desc && count) {
    count.textContent = desc.value.length;
    desc.addEventListener('input', () => { count.textContent = desc.value.length; });
  }

  // File upload
  const area       = document.getElementById(areaId);
  const fileInput  = document.getElementById(inputId);
  const previewDiv = document.getElementById(previewId);
  const previewImg = document.getElementById(previewImgId);
  const removeBtn  = document.getElementById(removeId);

  if (!area || !fileInput) return;

  function showPreview(file) {
    if (!file || !file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      if (previewImg) previewImg.src = e.target.result;
      if (previewDiv) previewDiv.style.display = 'block';
      area.querySelector('.file-upload-content').style.display = 'none';
    };
    reader.readAsDataURL(file);
  }

  fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) showPreview(fileInput.files[0]);
  });

  if (removeBtn) {
    removeBtn.addEventListener('click', (e) => {
      e.preventDefault();
      fileInput.value = '';
      if (previewDiv) previewDiv.style.display = 'none';
      area.querySelector('.file-upload-content').style.display = 'block';
    });
  }

  // Drag and drop
  ['dragenter','dragover'].forEach(evt => {
    area.addEventListener(evt, (e) => { e.preventDefault(); area.classList.add('drag-over'); });
  });
  ['dragleave','drop'].forEach(evt => {
    area.addEventListener(evt, (e) => { e.preventDefault(); area.classList.remove('drag-over'); });
  });
  area.addEventListener('drop', (e) => {
    const file = e.dataTransfer.files[0];
    if (file) {
      const dt = new DataTransfer();
      dt.items.add(file);
      fileInput.files = dt.files;
      showPreview(file);
    }
  });

  // Form validation
  const form = document.getElementById(formId);
  if (form) {
    form.addEventListener('submit', (e) => {
      let valid = true;
      form.querySelectorAll('[required]').forEach(input => {
        if (!input.value.trim()) {
          input.classList.add('is-invalid');
          valid = false;
        } else {
          input.classList.remove('is-invalid');
        }
      });
      if (!valid) {
        e.preventDefault();
        form.querySelectorAll('.is-invalid')[0]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else {
        const btn = form.querySelector('.btn-submit');
        if (btn) {
          btn.disabled = true;
          btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing…';
        }
      }
    });
    form.querySelectorAll('[required]').forEach(input => {
      input.addEventListener('input', () => input.classList.remove('is-invalid'));
    });
  }
}

/* ── Score ring animations on scroll ─────── */
function animateScoreRings() {
  document.querySelectorAll('.score-fill').forEach(el => {
    const target = el.style.strokeDasharray;
    el.style.strokeDasharray = '0 263.9';
    setTimeout(() => { el.style.strokeDasharray = target; }, 200);
  });
}
if (document.querySelector('.score-fill')) {
  setTimeout(animateScoreRings, 100);
}

/* ── Breakdown bar animations ─────────────── */
document.querySelectorAll('.breakdown-fill').forEach(bar => {
  const targetW = bar.style.width;
  bar.style.width = '0%';
  setTimeout(() => { bar.style.width = targetW; }, 300);
});

/* ── Flash auto-dismiss ───────────────────── */
setTimeout(() => {
  document.querySelectorAll('.flash-alert').forEach(alert => {
    const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
    if (bsAlert) bsAlert.close();
  });
}, 5000);

/* ── Tooltip init ─────────────────────────── */
document.querySelectorAll('[title]').forEach(el => {
  new bootstrap.Tooltip(el, { trigger: 'hover', placement: 'top' });
});

/* ── Card hover subtle lift ───────────────── */
document.querySelectorAll('.how-step').forEach(card => {
  card.addEventListener('mouseenter', () => {
    card.style.transform = 'translateY(-4px)';
    card.style.transition = 'transform .25s ease';
    card.style.borderColor = 'rgba(99,102,241,.3)';
  });
  card.addEventListener('mouseleave', () => {
    card.style.transform = '';
    card.style.borderColor = '';
  });
});
