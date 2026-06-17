/* =====================================================================
   Spiel Engine — DFY Qualification Wizard
   ===================================================================== */

(function () {
  'use strict';

  var SUCCESS_MSG = 'Subscribed ✓';
  var GOOGLE_FORM_ACTION = 'https://docs.google.com/forms/d/e/1FAIpQLScSAISdLXFTAex_cHMmdMCXQdaMGlwLouLRmptFo_5VcdV_GA/formResponse';
  var EMAIL_FIELD = 'entry.754901073';

  var currentStep = 1;
  var totalSteps = 7;
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
      els.counter.textContent = 'Step ' + n + ' of ' + totalSteps;
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
    var traffic = data['traffic'] || '';
    var budget = data['budget'] || '';
    var contentStatus = data['content_status'] || '';

    var rec = 'Based on what you shared, here\'s my recommendation for you:';

    var detail = '';
    if (contentStatus === 'no') {
      detail = 'You\'re not publishing yet — that\'s actually the best starting point. ';
      detail += 'The Spiel Engine DFY Install will set up your entire pipeline from scratch. ';
    } else if (contentStatus === 'irregular') {
      detail = 'You\'re publishing irregularly, which means the bottleneck is consistency, not quality. ';
      detail += 'The Spiel Engine automates the capture-to-draft pipeline so you never miss a session. ';
    } else {
      detail = 'You\'re already publishing consistently. The Spiel Engine will 10x your output ';
      detail += 'by turning every build session into a publishable asset automatically. ';
    }

    if (budget === 'under1k' || budget === '1to3k') {
      detail += 'The DFY Install at $2,900 fits your range and includes a 30-day review with a full refund guarantee.';
    } else if (budget === 'notsure') {
      detail += 'If budget is a concern, the open-source version is free. Clone it, customize it, and upgrade later.';
    } else {
      detail += 'At your budget level, I recommend the full DFY Install with priority support and custom agent configuration.';
    }

    var ctaText = 'Apply for DFY Install →';
    var ctaHref = '/contact/';
    var altText = 'or grab the open-source repo instead';
    var altHref = 'https://github.com/ShayanSpiel/SpielEngine';

    if (budget === 'under1k' || budget === 'notsure') {
      ctaText = 'Get the Open Source Repo →';
      ctaHref = 'https://github.com/ShayanSpiel/SpielEngine';
      altText = 'or learn about the DFY Install ($2,900)';
      altHref = '/contact/';
    }

    return { rec: rec, detail: detail, ctaText: ctaText, ctaHref: ctaHref, altText: altText, altHref: altHref };
  }

  function showResult(data) {
    var result = buildResult(data);
    if (els.resultStep) {
      els.steps.forEach(function (s) { s.classList.remove('active'); });
      els.resultStep.classList.add('active');
    }
    if (els.resultBody) {
      els.resultBody.innerHTML = '<p>' + result.rec + '</p><p>' + result.detail + '</p>';
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
    window.scrollTo({ top: els.wizard.offsetTop - 20, behavior: 'smooth' });
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

      // Submit to Google Forms
      var email = formData['email'] || '';
      if (email) {
        var iframe = document.getElementById('hidden_iframe');
        var form = document.createElement('form');
        form.method = 'POST';
        form.action = GOOGLE_FORM_ACTION;
        form.target = 'hidden_iframe';
        form.style.display = 'none';

        var input = document.createElement('input');
        input.type = 'hidden';
        input.name = EMAIL_FIELD;
        input.value = email;
        form.appendChild(input);

        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
      }

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
