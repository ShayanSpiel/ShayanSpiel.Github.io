(function () {
  const SHARE_URL = "https://geogent.spiel.workers.dev/?utm_source=twitter&utm_medium=share&utm_campaign=alpha_waitlist";
  const COPY_URL = "https://spielos.xyz/GeoGent-Waitlist/";
  const SHARE_TEXT = "I just locked in my @GeoGentX alpha seat. 🏰\n\nA browser strategy MMO where your rivals are AIs with memory, grudges, and personality. Real hex wars, real economy, no pay-to-win.\n\n1,000 founders. Limited seats. Grab yours 👇";
  const SHARE_HASHTAGS = "StrategyGames,IndieGame";
  const SUBMIT_TIMEOUT_MS = 6000;

  function setStatus(form, message, kind) {
    const el = form.querySelector(".form-status");
    if (!el) return;
    el.textContent = message;
    el.classList.remove("ok", "err");
    if (kind) el.classList.add(kind);
  }

  function lockButton(form, locked) {
    const btn = form.querySelector('button[type="submit"]');
    if (!btn) return;
    const lbl = btn.querySelector(".btn-label");
    if (locked) {
      if (lbl && !btn.dataset.label) btn.dataset.label = lbl.textContent;
      if (lbl) lbl.textContent = "Sending\u2026";
      btn.disabled = true;
    } else {
      if (lbl && btn.dataset.label) lbl.textContent = btn.dataset.label;
      btn.disabled = false;
    }
  }

  function showSuccess(form) {
    const wrap = form.closest("[data-form-wrap]");
    if (!wrap) return false;
    const success = wrap.querySelector("[data-form-success]");
    if (!success) return false;

    const head = wrap.querySelector("[data-success-head]");
    const body = wrap.querySelector("[data-success-body]");
    const share = wrap.querySelector("[data-success-share]");
    const copy = wrap.querySelector("[data-success-copy]");

    if (head) head.innerHTML = "You\u2019re in.";
    if (body) body.textContent = "We\u2019ll email you the moment alpha opens.";
    if (share) {
      const params = new URLSearchParams({
        text: SHARE_TEXT,
        url: SHARE_URL,
        hashtags: SHARE_HASHTAGS,
      });
      share.href = "https://twitter.com/intent/tweet?" + params.toString();
    }
    if (copy) {
      copy.addEventListener("click", function () {
        const label = copy.querySelector("[data-copy-label]");
        const doCopy = function () {
          if (label) label.textContent = "Copied \u2713";
          copy.classList.add("copied");
          setTimeout(function () {
            if (label) label.textContent = "Copy link";
            copy.classList.remove("copied");
          }, 1800);
        };
        const fallback = function () {
          const ta = document.createElement("textarea");
          ta.value = COPY_URL;
          ta.style.position = "fixed";
          ta.style.opacity = "0";
          document.body.appendChild(ta);
          ta.select();
          try { document.execCommand("copy"); } catch (e) {}
          document.body.removeChild(ta);
          doCopy();
        };
        if (navigator.clipboard && window.isSecureContext) {
          navigator.clipboard.writeText(COPY_URL).then(doCopy, fallback);
        } else {
          fallback();
        }
      });
    }

    form.hidden = true;
    success.hidden = false;
    return true;
  }

  const iframe = document.getElementById("hidden_iframe");
  const forms = document.querySelectorAll("form.waitlist");

  let pendingForm = null;
  let pendingTimeoutId = null;

  function failPending() {
    if (!pendingForm) return;
    const form = pendingForm;
    pendingForm = null;
    setStatus(form, "Hmm, didn\u2019t go through. Check your connection and retry.", "err");
    lockButton(form, false);
    form.querySelector('input[type="email"]')?.focus();
  }

  if (iframe) {
    iframe.addEventListener("load", function () {
      if (pendingTimeoutId) {
        clearTimeout(pendingTimeoutId);
        pendingTimeoutId = null;
      }
      if (!pendingForm) return;
      const form = pendingForm;
      pendingForm = null;
      showSuccess(form);
    });
  }

  forms.forEach((form) => {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      const input = form.querySelector('input[type="email"]');
      const email = (input?.value || "").trim();
      if (!email) {
        setStatus(form, "Please enter your email.", "err");
        input?.focus();
        return;
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        setStatus(form, "That email doesn\u2019t look right.", "err");
        input?.focus();
        return;
      }

      if (pendingTimeoutId) {
        clearTimeout(pendingTimeoutId);
        pendingTimeoutId = null;
      }
      pendingForm = form;
      setStatus(form, "");
      lockButton(form, true);
      pendingTimeoutId = setTimeout(failPending, SUBMIT_TIMEOUT_MS);
      form.submit();
    });
  });
})();
