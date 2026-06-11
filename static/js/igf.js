// IGF Sadhana Tracker – Main JS

document.addEventListener('DOMContentLoaded', function () {

  // ── Sidebar toggle ──────────────────────────
  const sidebar  = document.getElementById('sidebar');
  const overlay  = document.getElementById('sidebarOverlay');
  const menuBtn  = document.getElementById('menuToggle');

  function openSidebar() {
    sidebar?.classList.add('open');
    overlay?.classList.add('show');
  }
  function closeSidebar() {
    sidebar?.classList.remove('open');
    overlay?.classList.remove('show');
  }

  menuBtn?.addEventListener('click', openSidebar);
  overlay?.addEventListener('click', closeSidebar);

  // ── Mark active nav link ────────────────────
  const path = window.location.pathname;
  document.querySelectorAll('.sidebar-nav a').forEach(link => {
    if (link.getAttribute('href') === path ||
        (path.startsWith(link.getAttribute('href')) && link.getAttribute('href') !== '/')) {
      link.classList.add('active');
    }
  });

  // ── Auto-dismiss alerts ─────────────────────
  document.querySelectorAll('.alert-autohide').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity .5s';
      el.style.opacity    = '0';
      setTimeout(() => el.remove(), 500);
    }, 3500);
  });

  // ── Notification bell ───────────────────────
  const notifBtn = document.getElementById('notifBtn');
  notifBtn?.addEventListener('click', function () {
    fetch('/api/notifications/read/', {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken') }
    }).then(() => {
      const dot = document.querySelector('.notif-dot');
      if (dot) dot.remove();
    });
  });

  // ── CSRF helper ─────────────────────────────
  function getCookie(name) {
    let v = null;
    document.cookie.split(';').forEach(c => {
      const [k, val] = c.trim().split('=');
      if (k === name) v = decodeURIComponent(val);
    });
    return v;
  }

  // ── Chant count quick-increment ─────────────
  const chantInput = document.getElementById('id_chant_count');
  if (chantInput) {
    const minus = document.getElementById('chantMinus');
    const plus  = document.getElementById('chantPlus');
    minus?.addEventListener('click', () => {
      const v = parseInt(chantInput.value) || 0;
      if (v > 0) chantInput.value = v - 1;
    });
    plus?.addEventListener('click', () => {
      const v = parseInt(chantInput.value) || 0;
      if (v < 64) chantInput.value = v + 1;
    });
  }

  // ── Mangal Arati toggle visual ──────────────
  const maSwitch = document.getElementById('id_mangal_arati');
  if (maSwitch) {
    const label = document.getElementById('maLabel');
    function updateMA() {
      if (label) label.textContent = maSwitch.checked ? '✅ Attended' : '❌ Not attended';
    }
    maSwitch.addEventListener('change', updateMA);
    updateMA();
  }

  // ── Analytics Charts ─────────────────────────
  const analyticsCanvas = document.getElementById('analyticsChart');
  if (analyticsCanvas) {
    loadAnalytics();
  }

  async function loadAnalytics() {
    const days = document.getElementById('analyticsDays')?.value || 30;
    const res  = await fetch(`/api/analytics/?days=${days}`);
    const data = await res.json();
    renderAnalyticsCharts(data);
  }

  function renderAnalyticsCharts(data) {
    // Chanting chart
    const chantCtx = document.getElementById('chantChart');
    if (chantCtx) {
      new Chart(chantCtx, {
        type: 'line',
        data: {
          labels: data.labels,
          datasets: [{
            label: 'Avg Rounds',
            data: data.chant,
            borderColor: '#F06292',
            backgroundColor: 'rgba(240,98,146,.1)',
            fill: true,
            tension: .4,
            pointRadius: 3,
          }]
        },
        options: { responsive: true, plugins: { legend: { display: false } } }
      });
    }

    // Reading & Hearing chart
    const readHearCtx = document.getElementById('readHearChart');
    if (readHearCtx) {
      new Chart(readHearCtx, {
        type: 'bar',
        data: {
          labels: data.labels,
          datasets: [
            {
              label: 'Reading (min)',
              data: data.reading,
              backgroundColor: 'rgba(255,160,122,.7)',
            },
            {
              label: 'Hearing (min)',
              data: data.hearing,
              backgroundColor: 'rgba(248,187,208,.7)',
            }
          ]
        },
        options: {
          responsive: true,
          plugins: { legend: { position: 'bottom' } },
          scales: { x: { stacked: false }, y: { beginAtZero: true } }
        }
      });
    }

    // Submissions chart
    const submCtx = document.getElementById('submissionsChart');
    if (submCtx) {
      new Chart(submCtx, {
        type: 'bar',
        data: {
          labels: data.labels,
          datasets: [{
            label: 'Submissions',
            data: data.submissions,
            backgroundColor: 'rgba(165,214,167,.8)',
            borderColor: '#4CAF50',
            borderWidth: 1,
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: { y: { beginAtZero: true } }
        }
      });
    }
  }

  // ── Days selector for analytics ──────────────
  document.getElementById('analyticsDays')?.addEventListener('change', loadAnalytics);

  // ── Progress circle ──────────────────────────
  document.querySelectorAll('.progress-circle').forEach(el => {
    const pct = parseFloat(el.dataset.pct) || 0;
    const r   = 36;
    const circ = 2 * Math.PI * r;
    const dash  = (pct / 100) * circ;
    el.style.setProperty('--dash', dash);
    el.style.setProperty('--circ', circ);
  });

  // ── Confirm delete ─────────────────────────
  document.querySelectorAll('.confirm-delete').forEach(btn => {
    btn.addEventListener('click', e => {
      if (!confirm('Are you sure? This action cannot be undone.')) e.preventDefault();
    });
  });

});
