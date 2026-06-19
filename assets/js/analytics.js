/* =====================================================================
   Analytics & Event Tracking — Production-grade GA4 integration
   =====================================================================
   Event taxonomy:
     page_view            — automatic via gtag
     copy_homebrew_command — user copies brew install command
     copy_cli_command      — user copies any CLI command
     click_install        — user clicks install/get button
     click_docs           — user clicks documentation link
     click_github         — user clicks GitHub link
     click_contact        — user clicks contact link
     click_demo           — user clicks demo link
     cta_primary_clicked  — primary CTA clicked
     cta_secondary_clicked — secondary CTA clicked
     newsletter_subscribe — newsletter form submitted
     scroll_depth         — 25/50/75/100% scroll reached
     ab_test_assigned     — user assigned to A/B variant
     FAQ opened           — FAQ accordion opened
   ===================================================================== */

(function () {
  'use strict';

  /* ---- Helpers ---- */
  function track(eventName, params) {
    if (typeof gtag === 'function') {
      gtag('event', eventName, params || {});
    }
  }

  function getPage() {
    return window.location.pathname;
  }

  function getDevice() {
    var w = window.innerWidth;
    if (w < 768) return 'mobile';
    if (w < 1024) return 'tablet';
    return 'desktop';
  }

  function getVariant() {
    try { return localStorage.getItem('ab_variant') || 'control'; }
    catch (e) { return 'control'; }
  }

  /* ================================================================
     A/B TEST: Landing Page Copy Variants
     ================================================================
     Cycles through variants on each page load for testing.
     In production, swap to sticky assignment (see commented code).
     ================================================================ */

  var AB_KEY = 'ab_variant';
  var VARIANTS = ['control', 'variant_a', 'variant_b', 'variant_c'];

  function assignVariant() {
    try {
      /* CYCLE MODE: advances each page load so refresh shows next variant */
      var idx = parseInt(localStorage.getItem(AB_KEY + '_idx'), 10);
      if (isNaN(idx) || idx >= VARIANTS.length) idx = 0;
      var v = VARIANTS[idx];
      localStorage.setItem(AB_KEY, v);
      localStorage.setItem(AB_KEY + '_idx', String((idx + 1) % VARIANTS.length));
      return v;

      /* STICKY MODE: uncomment below, comment above, for production
      var existing = localStorage.getItem(AB_KEY);
      if (existing && VARIANTS.indexOf(existing) !== -1) return existing;
      var v = VARIANTS[Math.floor(Math.random() * VARIANTS.length)];
      localStorage.setItem(AB_KEY, v);
      return v;
      */
    } catch (e) {
      return 'control';
    }
  }

  var variant = assignVariant();

  /* Variant copy — bite-sized, positioning-aligned */
  var COPY = {
    control: {
      headline: 'Work Is Content.',
      subheadline: 'Spiel Engine turns your coding sessions into publishable content. No extra effort.',
      supporting: 'Capture. Simulate. <span class="hl">Publish.</span>'
    },
    variant_a: {
      headline: 'You\'re Already Creating Content.',
      subheadline: 'Every session, commit, and decision is content. Spiel just publishes it for you.',
      supporting: 'Stop choosing between building <span class="hl">and posting.</span>'
    },
    variant_b: {
      headline: 'Every Commit Is Marketing.',
      subheadline: 'Your build sessions are your best marketing material. Spiel captures and publishes them.',
      supporting: 'Develop. Ship. <span class="hl">It publishes.</span>'
    },
    variant_c: {
      headline: 'Builders Don\'t Write Content.',
      subheadline: 'They ship code. Spiel turns what you already do into content that reaches people.',
      supporting: 'Build. <span class="hl">Spiel handles the rest.</span>'
    }
  };

  /* Apply variant copy to DOM */
  function applyVariant() {
    var c = COPY[variant];
    if (!c) return;

    var heroH1 = document.querySelector('[data-ab="hero-headline"]');
    var heroSub = document.querySelector('[data-ab="hero-sub"]');
    var supportH2 = document.querySelector('[data-ab="support-headline"]');

    if (heroH1) heroH1.innerHTML = c.headline;
    if (heroSub) heroSub.textContent = c.subheadline;
    if (supportH2) supportH2.innerHTML = c.supporting;

    /* Track assignment */
    track('ab_test_assigned', {
      variant: variant,
      page: getPage(),
      device: getDevice()
    });
  }

  /* ================================================================
     CLICK EVENT TRACKING
     ================================================================ */

  function trackClick(selector, eventName, extraProps) {
    document.querySelectorAll(selector).forEach(function (el) {
      el.addEventListener('click', function () {
        var props = Object.assign({ page: getPage(), device: getDevice(), variant: variant }, extraProps || {});
        track(eventName, props);
      });
    });
  }

  /* Homebrew copy commands */
  function setupCopyTracking() {
    document.querySelectorAll('.cli-box').forEach(function (box) {
      box.addEventListener('click', function () {
        var cmd = box.querySelector('.cmd');
        var cmdText = cmd ? cmd.textContent.trim() : '';
        var eventName = cmdText.indexOf('brew') !== -1 ? 'copy_homebrew_command' : 'copy_cli_command';
        track(eventName, {
          page: getPage(),
          command: cmdText,
          variant: variant,
          device: getDevice()
        });
      });
    });
  }

  /* Install buttons — hero and mid-page install CTAs on SpielEngine */
  trackClick('.hero .btn-primary, .title-copy .btn-primary', 'click_install');

  /* GitHub links */
  trackClick('a[href*="github.com"]', 'click_github');

  /* Contact links */
  trackClick('a[href*="contact"]', 'click_contact');

  /* Documentation links */
  trackClick('a[href*="docs"], a[href*="readme"]', 'click_docs');

  /* CTA primary — all primary action buttons (includes install) */
  document.querySelectorAll('.btn-primary, .card-btn, .cta-btn').forEach(function (el) {
    el.addEventListener('click', function () {
      var section = el.closest('section');
      var sectionName = section ? (section.id || section.className.split(' ')[0]) : 'unknown';
      track('cta_primary_clicked', {
        page: getPage(),
        device: getDevice(),
        variant: variant,
        section: sectionName
      });
    });
  });

  /* CTA secondary (btn-ghost class) */
  trackClick('.btn-ghost', 'cta_secondary_clicked');

  /* FAQ tracking */
  document.querySelectorAll('.faq-q').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var card = this.closest('.faq-card');
      var question = this.textContent.trim();
      track('FAQ_opened', {
        page: getPage(),
        question: question,
        variant: variant
      });
    });
  });

  /* Newsletter subscribe */
  var nlForm = document.getElementById('subscribe');
  if (nlForm) {
    nlForm.addEventListener('submit', function () {
      track('newsletter_subscribe', { page: getPage(), device: getDevice() });
    });
  }

  /* ================================================================
     SCROLL DEPTH TRACKING
     ================================================================ */

  function setupScrollTracking() {
    var thresholds = [25, 50, 75, 100];
    var fired = {};

    function checkScroll() {
      var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      var docHeight = Math.max(
        document.body.scrollHeight,
        document.documentElement.scrollHeight
      );
      var winHeight = window.innerHeight;
      var scrollPercent = Math.round((scrollTop / (docHeight - winHeight)) * 100);

      thresholds.forEach(function (t) {
        if (!fired[t] && scrollPercent >= t) {
          fired[t] = true;
          track('scroll_depth', {
            page: getPage(),
            depth: t,
            variant: variant,
            device: getDevice()
          });
        }
      });
    }

    window.addEventListener('scroll', checkScroll, { passive: true });
    checkScroll();
  }

  /* ================================================================
     INIT
     ================================================================ */

  /* Apply A/B variant on SpielEngine page */
  var isSpielEngine = window.location.pathname.indexOf('SpielEngine') !== -1;
  if (isSpielEngine) {
    applyVariant();
  }

  /* Setup all tracking */
  setupCopyTracking();
  setupScrollTracking();

  /* Track outbound links */
  document.querySelectorAll('a[target="_blank"]').forEach(function (el) {
    el.addEventListener('click', function () {
      track('outbound_link', {
        url: this.href,
        page: getPage(),
        variant: variant
      });
    });
  });

})();
