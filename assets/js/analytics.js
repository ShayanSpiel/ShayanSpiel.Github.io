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
     Control: Current copy
     Variant A: "Work → Content" angle
     Variant B: "Developer Marketing" angle
     ================================================================ */

  var AB_KEY = 'ab_variant';
  var VARIANTS = ['control', 'variant_a', 'variant_b'];

  function assignVariant() {
    try {
      var existing = localStorage.getItem(AB_KEY);
      if (existing && VARIANTS.indexOf(existing) !== -1) return existing;
      var variant = VARIANTS[Math.floor(Math.random() * VARIANTS.length)];
      localStorage.setItem(AB_KEY, variant);
      return variant;
    } catch (e) {
      return 'control';
    }
  }

  var variant = assignVariant();

  /* Variant copy definitions */
  var COPY = {
    control: {
      headline: 'Capture. Simulate.<br><span class="hl">Publish.</span>',
      subheadline: 'Your coding sessions are already content. Spiel Engine extracts it, in your voice, for your audience, and publish instantly across every platform.',
      supporting: 'Turn your build sessions into content, <span class="hl">without being a marketer.</span>'
    },
    variant_a: {
      headline: 'You already create content.<br><span class="hl">You just don\'t publish it.</span>',
      subheadline: 'Most creators stop working to create content. Spiel removes that tradeoff. Your sessions, commits, and decisions become publishable content — automatically.',
      supporting: 'Stop choosing between building <span class="hl">and publishing.</span>'
    },
    variant_b: {
      headline: 'Every commit is marketing.<br><span class="hl">Every build is marketing.</span>',
      subheadline: 'The fastest-growing builders don\'t create content. They capture it. Spiel Engine turns your development activity into content that ships with your code.',
      supporting: 'The best builders <span class="hl">don\'t create content. They capture it.</span>'
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
