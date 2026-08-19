/*
  VANTAGE — vantage-theme.js
  Único componente de theme toggle compartido por dashboard.html y Checklist.html.
  Resuelve dos Fails de la auditoría 2026-07-10:
    1. El tema no persistía entre recargas (siempre iniciaba en 'dark').
    2. No había sincronía cross-tab (cambiar tema en una pestaña no afectaba la otra).
*/
(function () {
  const KEY = 'vantage-theme';
  const html = document.documentElement;

  const ICON_MOON = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
  const ICON_SUN  = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>';

  let theme = localStorage.getItem(KEY) ||
    (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');

  function applyTheme(t) {
    html.setAttribute('data-theme', t);
    const toggle = document.querySelector('[data-theme-toggle]');
    if (toggle) toggle.innerHTML = t === 'dark' ? ICON_MOON : ICON_SUN;
  }

  applyTheme(theme);

  document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.querySelector('[data-theme-toggle]');
    if (!toggle) return;
    toggle.innerHTML = theme === 'dark' ? ICON_MOON : ICON_SUN;
    toggle.addEventListener('click', () => {
      theme = theme === 'dark' ? 'light' : 'dark';
      localStorage.setItem(KEY, theme);
      applyTheme(theme);
    });
  });

  // Sync cross-tab: si otra pestaña de VANTAGE cambia el tema, esta lo refleja sin reload.
  window.addEventListener('storage', (e) => {
    if (e.key === KEY && e.newValue) {
      theme = e.newValue;
      applyTheme(theme);
    }
  });
})();
