(function() {
  'use strict';
  var KEY = 'site-lang';

  function getStoredLang() {
    var lang = localStorage.getItem(KEY);
    return (lang === 'zh' || lang === 'en') ? lang : 'zh';
  }

  function setLang(lang) {
    if (lang !== 'zh' && lang !== 'en') return;
    localStorage.setItem(KEY, lang);

    // 1. Set html lang attribute — CSS handles all .lang-content visibility
    var htmlLang = lang === 'zh' ? 'zh-CN' : 'en';
    document.documentElement.setAttribute('lang', htmlLang);

    // 2. Toggle text-only elements (data-lang-zh / data-lang-en)
    document.querySelectorAll('[data-lang-zh][data-lang-en]').forEach(function(el) {
      var target = el.getAttribute('data-lang-' + lang);
      if (!target) return;
      var tag = el.tagName;
      if (tag === 'TITLE') {
        document.title = target;
      } else if (tag === 'INPUT' || tag === 'TEXTAREA') {
        el.setAttribute('placeholder', target);
      } else if (tag === 'A' && el.querySelector('img')) {
        // anchor with image child: only change text nodes, not innerHTML
        el.childNodes.forEach(function(node) {
          if (node.nodeType === Node.TEXT_NODE && node.textContent.trim()) {
            node.textContent = target;
          }
        });
      } else {
        el.textContent = target;
      }
    });

    // 3. Update buttons
    document.querySelectorAll('.lang-btn').forEach(function(btn) {
      var btnLang = btn.getAttribute('data-lang');
      if (!btnLang) {
        btnLang = btn.id === 'btnZh' ? 'zh' : btn.id === 'btnEn' ? 'en' : null;
      }
      if (!btnLang) return;
      var active = btnLang === lang;
      btn.classList.toggle('lang-btn--active', active);
      btn.setAttribute('aria-pressed', active ? 'true' : 'false');
      if (active) {
        btn.setAttribute('aria-current', 'true');
      } else {
        btn.removeAttribute('aria-current');
      }
    });

    // 4. Dispatch custom event for other components
    window.dispatchEvent(new CustomEvent('langchange', { detail: { lang: lang } }));
  }

  window.setLang = setLang;

  document.addEventListener('DOMContentLoaded', function() {
    // Inject nav language switcher if not already present
    var nav = document.querySelector('.nav__inner');
    if (nav && !nav.querySelector('.lang-switch')) {
      var switcher = document.createElement('div');
      switcher.className = 'lang-switch';
      switcher.innerHTML =
        '<button class="lang-btn" data-lang="zh" onclick="setLang(\'zh\')" aria-label="Switch to Chinese" aria-pressed="false">中文</button>' +
        '<span class="lang-divider" aria-hidden="true">|</span>' +
        '<button class="lang-btn" data-lang="en" onclick="setLang(\'en\')" aria-label="Switch to English" aria-pressed="false">EN</button>';
      nav.appendChild(switcher);
    }
    setLang(getStoredLang());
  });
})();
