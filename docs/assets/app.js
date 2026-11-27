// Essentials for Financial Derivatives — UI, KaTeX, and Navigation Controller
(function () {
  // 1. Theme persistence
  const root = document.documentElement;
  const savedTheme = localStorage.getItem('efd-theme');
  if (savedTheme) {
    root.setAttribute('data-theme', savedTheme);
  } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    root.setAttribute('data-theme', 'dark');
  }

  function updateThemeBtn() {
    const btn = document.getElementById('theme-toggle');
    if (!btn) return;
    const isDark = root.getAttribute('data-theme') === 'dark';
    btn.textContent = isDark ? 'Light mode' : 'Dark mode';
  }

  document.addEventListener('DOMContentLoaded', () => {
    updateThemeBtn();

    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn) {
      themeBtn.addEventListener('click', () => {
        const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        root.setAttribute('data-theme', next);
        localStorage.setItem('efd-theme', next);
        updateThemeBtn();
        window.dispatchEvent(new CustomEvent('efd-theme-change', { detail: { theme: next } }));
      });
    }

    // 2. Mobile sidebar drawer
    const menuBtn = document.getElementById('menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    if (menuBtn && sidebar) {
      menuBtn.addEventListener('click', () => sidebar.classList.toggle('open'));
      document.addEventListener('click', (e) => {
        if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && !menuBtn.contains(e.target)) {
          sidebar.classList.remove('open');
        }
      });
    }

    // 3. Sidebar search filter
    const searchInput = document.getElementById('nav-search');
    if (searchInput) {
      searchInput.addEventListener('input', () => {
        const q = searchInput.value.trim().toLowerCase();
        document.querySelectorAll('.nav-list li').forEach((li) => {
          li.style.display = li.textContent.toLowerCase().includes(q) ? '' : 'none';
        });
      });
    }

    // 4. Render KaTeX with all macros matching outline.tex (use \[...\] and \(...\) only so literal currency $ never triggers math mode)
    if (window.renderMathInElement) {
      renderMathInElement(document.body, {
        delimiters: [
          { left: '\\[', right: '\\]', display: true },
          { left: '\\(', right: '\\)', display: false }
        ],
        throwOnError: false,
        strict: false,
        macros: {
          '\\E': '\\mathbb{E}',
          '\\Prob': '\\mathbb{P}',
          '\\Q': '\\mathbb{Q}',
          '\\R': '\\mathbb{R}',
          '\\N': '\\mathbb{N}',
          '\\F': '\\mathcal{F}',
          '\\dd': '\\,\\mathrm{d}',
          '\\ind': '\\mathbf{1}',
          '\\Var': '\\operatorname{Var}',
          '\\Cov': '\\operatorname{Cov}',
          '\\BS': '\\operatorname{BS}',
          '\\symbf': '\\boldsymbol'
        }
      });
    }

    // 5. Initialize interactive quant labs if present
    if (window.initQuantLabs) {
      window.initQuantLabs();
    }
  });
})();
