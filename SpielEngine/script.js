/* =====================================================================
   Spiel Engine — DFY Qualification Wizard
   ===================================================================== */

(function () {
  'use strict';

  var GOOGLE_FORM_ACTION = 'https://docs.google.com/forms/d/e/1FAIpQLScSAISdLXFTAex_cHMmdMCXQdaMGlwLouLRmptFo_5VcdV_GA/formResponse';
  var FORM_FIELDS = {
    name: 'entry.1115130739',
    email: 'entry.754901073',
    build: 'entry.1797830417',
    content_status: 'entry.2013515666',
    budget: 'entry.1908783944',
    source: 'entry.2021940811'
  };

  var currentStep = 1;
  var totalSteps = 5;
  var formData = {};

  var els = {
    wizard: document.getElementById('wizard'),
    steps: document.querySelectorAll('.wizard-step'),
    dots: document.querySelectorAll('.wizard-step-dot'),
    counter: document.getElementById('stepCounter'),
    nextBtn: document.getElementById('wizardNext'),
    prevBtn: document.getElementById('wizardPrev'),
    submitBtn: document.getElementById('wizardSubmit'),
    form: document.getElementById('wizardForm'),
    resultStep: document.getElementById('wizardResult'),
    resultBody: document.getElementById('resultBody'),
    resultCta: document.getElementById('resultCta'),
    resultAlt: document.getElementById('resultAlt'),
  };

  if (!els.wizard) return;

  function showStep(n) {
    els.steps.forEach(function (s, i) {
      s.classList.toggle('active', i + 1 === n);
    });
    els.dots.forEach(function (d, i) {
      d.classList.toggle('active', i + 1 === n);
      d.classList.toggle('done', i + 1 < n);
    });
    if (els.counter) {
      els.counter.textContent = n + ' of ' + totalSteps;
    }
    // Show/hide buttons
    if (els.prevBtn) els.prevBtn.style.display = n === 1 ? 'none' : 'inline-flex';
    if (els.nextBtn) els.nextBtn.style.display = n === totalSteps ? 'none' : 'inline-flex';
    if (els.submitBtn) els.submitBtn.style.display = n === totalSteps ? 'inline-flex' : 'none';

    currentStep = n;
    window.scrollTo({ top: els.wizard.offsetTop - 20, behavior: 'smooth' });
  }

  function collectStepData(n) {
    var step = els.steps[n - 1];
    if (!step) return;
    var inputs = step.querySelectorAll('input, textarea, select');
    inputs.forEach(function (inp) {
      if (inp.type === 'radio') {
        if (inp.checked) formData[inp.name] = inp.value;
      } else if (inp.type === 'checkbox') {
        formData[inp.name] = inp.checked;
      } else {
        var val = inp.value.trim();
        if (val) formData[inp.name] = val;
      }
    });
  }

  function validateStep(n) {
    var step = els.steps[n - 1];
    if (!step) return true;
    var inputs = step.querySelectorAll('input[required], textarea[required], select[required]');
    for (var i = 0; i < inputs.length; i++) {
      var inp = inputs[i];
      if (inp.type === 'radio') {
        var name = inp.name;
        var checked = step.querySelector('input[name="' + name + '"]:checked');
        if (!checked) {
          highlightError(inp);
          return false;
        }
      } else if (inp.type === 'email') {
        var val = inp.value.trim();
        if (!val || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) {
          highlightError(inp);
          return false;
        }
      } else if (!inp.value.trim()) {
        highlightError(inp);
        return false;
      }
    }
    return true;
  }

  function highlightError(inp) {
    inp.style.borderColor = '#FF6A00';
    inp.focus();
    setTimeout(function () { inp.style.borderColor = ''; }, 2000);
  }

  function handleRadioSelection() {
    document.querySelectorAll('.radio-group').forEach(function (group) {
      group.addEventListener('click', function (e) {
        var option = e.target.closest('.radio-option');
        if (!option) return;
        var radio = option.querySelector('input[type="radio"]');
        if (radio) {
          radio.checked = true;
          group.querySelectorAll('.radio-option').forEach(function (o) {
            o.classList.toggle('selected', o === option);
          });
        }
      });
    });
  }

  function buildResult(data) {
    var budget = data['budget'] || '';
    var contentStatus = data['content_status'] || '';
    var name = data['name'] || 'there';

    var detail = '';
    if (contentStatus === 'no') {
      detail = 'You\u2019re not publishing yet \u2014 that\u2019s the best starting point. The Spiel Engine DFY Install builds your pipeline from scratch. You get positioning, agent config, templates, and 30 days of iteration.';
    } else if (contentStatus === 'irregular') {
      detail = 'Your bottleneck is consistency, not quality. The Spiel Engine automates capture-to-draft so every session produces something publishable. No more starting from zero.';
    } else {
      detail = 'You\u2019re already publishing. The Spiel Engine turns every build session into a publishable asset automatically \u2014 so you 10x output without working more.';
    }

    var ctaText = '\u{1F4AC} DM me on X for questions';
    var ctaHref = 'https://x.com/i/chat/3477724042-3477724042';
    var altText = 'or get the open-source Spiel Engine';
    var altHref = 'https://github.com/ShayanSpiel/SpielEngine';

    if (budget === 'under1k' || budget === 'notsure') {
      ctaText = '\u{1F680} Get the open-source Spiel Engine';
      ctaHref = 'https://github.com/ShayanSpiel/SpielEngine';
      altText = '\u{1F4AC} Or DM me on X with questions';
      altHref = 'https://x.com/i/chat/3477724042-3477724042';
    }

    return { rec: name, detail: detail, ctaText: ctaText, ctaHref: ctaHref, altText: altText, altHref: altHref };
  }

  function showResult(data) {
    var result = buildResult(data);
    if (els.wizard) els.wizard.style.display = 'none';
    if (els.resultStep) {
      els.resultStep.style.display = 'block';
    }
    if (els.resultBody) {
      els.resultBody.innerHTML = '<p><strong>' + result.rec + '</strong>, here\u2019s what I recommend:</p><p>' + result.detail + '</p>';
    }
    if (els.resultCta) {
      els.resultCta.href = result.ctaHref;
      els.resultCta.textContent = result.ctaText;
    }
    if (els.resultAlt) {
      els.resultAlt.href = result.altHref;
      els.resultAlt.textContent = result.altText;
      els.resultAlt.style.display = 'inline';
    }
    if (els.counter) els.counter.style.display = 'none';
    if (els.dots) {
      els.dots.forEach(function (d) { d.style.display = 'none'; });
    }
    var scrollTarget = els.resultStep || els.wizard;
    window.scrollTo({ top: scrollTarget.offsetTop - 40, behavior: 'smooth' });
  }

  // Next button
  if (els.nextBtn) {
    els.nextBtn.addEventListener('click', function () {
      if (!validateStep(currentStep)) return;
      collectStepData(currentStep);
      showStep(currentStep + 1);
    });
  }

  // Previous button
  if (els.prevBtn) {
    els.prevBtn.addEventListener('click', function () {
      collectStepData(currentStep);
      showStep(currentStep - 1);
    });
  }

  // Submit button
  if (els.submitBtn) {
    els.submitBtn.addEventListener('click', function () {
      if (!validateStep(currentStep)) return;
      collectStepData(currentStep);

      // Submit all data to Google Forms
      var iframe = document.getElementById('hidden_iframe');
      var form = document.createElement('form');
      form.method = 'POST';
      form.action = GOOGLE_FORM_ACTION;
      form.target = 'hidden_iframe';
      form.style.display = 'none';

      function addField(name, value) {
        var el = document.createElement('input');
        el.type = 'hidden';
        el.name = name;
        el.value = value || '';
        form.appendChild(el);
      }

      addField(FORM_FIELDS.name, formData['name']);
      addField(FORM_FIELDS.email, formData['email']);
      addField(FORM_FIELDS.build, formData['build']);
      addField(FORM_FIELDS.content_status, formData['content_status']);
      addField(FORM_FIELDS.budget, formData['budget']);
      addField(FORM_FIELDS.source, 'Landing');

      document.body.appendChild(form);
      form.submit();
      document.body.removeChild(form);

      showResult(formData);
    });
  }

  // Keyboard support
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
      var active = document.activeElement;
      if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.tagName === 'SELECT')) {
        e.preventDefault();
        if (currentStep === totalSteps) {
          if (els.submitBtn) els.submitBtn.click();
        } else {
          if (els.nextBtn) els.nextBtn.click();
        }
      }
    }
  });

  // Init
  handleRadioSelection();
  showStep(1);

})();
