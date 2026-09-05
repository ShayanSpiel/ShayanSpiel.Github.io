// ChatAssistant runtime (vanilla, no framework island).
// Contract with the Supabase Edge Function `chat` (supabase/functions/chat):
//   POST {functionUrl} { messages:[{role,content}...], locale, session_id }
//   SSE: data: {"delta":"..."} | {"capture":true,"thanks_line":"..."} |
//             {"done":true,"reply_id":"..."} | {"error":"..."}(within done)
// v1: transient session (per page load), history client-held, capped 16.
(function () {
  "use strict";

  var root = document.querySelector("chat-assistant");
  if (!root) return;
  var url = root.getAttribute("data-function-url");
  var locale = root.getAttribute("data-locale") || "en";
  if (!url) return;

  var els = {
    launcher: document.getElementById("chat-launcher"),
    sheet: document.getElementById("chat-sheet"),
    backdrop: document.getElementById("chat-backdrop"),
    close: document.getElementById("chat-close"),
    messages: document.getElementById("chat-messages"),
    composer: document.getElementById("chat-composer"),
    input: document.getElementById("chat-input"),
    send: document.getElementById("chat-send"),
  };
  if (!els.launcher || !els.sheet) return;

  var i18n = {};
  try {
    i18n = JSON.parse(document.getElementById("chat-i18n").textContent || "{}");
  } catch (e) { /* strings degrade to EN */ }
  function T(key, fallback) { return i18n[key] || fallback || key; }

  var ALLOWLIST = (window.SPIELOS_CHAT_LINKS && window.SPIELOS_CHAT_LINKS.link_allowlist) || [];
  var CTA = (window.SPIELOS_CHAT_LINKS && window.SPIELOS_CHAT_LINKS.cta) || {};

  /* ---------- returning-visitor recognition (cookie, 180d) ---------- */
  var COOKIE = "spielos_chat_contact";
  function readCookieContact() {
    try {
      var m = document.cookie.match(new RegExp("(?:^|; )" + COOKIE + "=([^;]*)"));
      if (!m) return null;
      return JSON.parse(decodeURIComponent(m[1]));
    } catch (e) { return null; }
  }
  function writeCookieContact(c) {
    try {
      var val = encodeURIComponent(JSON.stringify(c));
      document.cookie = COOKIE + "=" + val + ";max-age=15552000;path=/;SameSite=Lax";
    } catch (e) {}
  }

  var state = {
    history: [],          // {role, content} sent to the function
    assistantReplies: 0, // drives the one-time ask (after the FIRST reply)
    captureShown: false,
    captureDone: false,
    known: null,          // returning-visitor contact from cookie
    streaming: false,
    open: false,
    session: (crypto.randomUUID && crypto.randomUUID()) || ("s-" + Date.now() + "-" + Math.random().toString(36).slice(2, 10)),
    turnCount: 0,
  };
  (function () {
    var c = readCookieContact();
    if (c && (c.name || c.email || c.phone)) state.known = c;
  })();

  /* ---------- helpers ---------- */
  function track(name, props) {
    if (typeof window.spielosTrack === "function") {
      try { window.spielosTrack(name, props || {}); } catch (e) {}
    }
  }
  function getDevice() {
    var w = window.innerWidth;
    if (w < 768) return "mobile";
    if (w < 1024) return "tablet";
    return "desktop";
  }
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  /* ---------- markdown-lite: [label](href) with allowlist ---------- */
  var LINK_RE = /\[([^\]]{1,120})\]\((\/[^)\s]{0,240})\)/g;
  function renderRich(text) {
    var html = escapeHtml(text);
    // Normalize absolute site URLs to site-relative before matching, so the
    // model's absolute hrefs still hit the allowlist (which is site-relative).
    html = html.replace(/\]\(https:\/\/spielos\.xyz(\/[^)\s]*)\)/g, "]($1)");
    html = html.replace(LINK_RE, function (m, label, href) {
      if (ALLOWLIST.indexOf(href) === -1) return label; // un-allowlisted: label only
      return '<a href="' + href + '" class="chat-msg-link" data-chat-nav>' + label + "</a>";
    });
    // bold + inline code for a bit of life in replies
    html = html.replace(/\*\*([^*\n]{1,120})\*\*/g, "<strong>$1</strong>");
    html = html.replace(/`([^`\n]{1,80})`/g, "<code>$1</code>");
    return html;
  }

  /* ---------- drawer/menu awareness (FAB hide) ---------- */
  function doorOpen() {
    var fn = document.getElementById("feature-nav-toggle");
    var navMenu = document.getElementById("nav-mobile-menu");
    return !!(
      (fn && fn.getAttribute("aria-expanded") === "true") ||
      (navMenu && !navMenu.classList.contains("hidden")) ||
      document.body.style.overflow === "hidden" ||
      document.documentElement.style.overflow === "hidden"
    );
  }
  var doorObserver = new MutationObserver(syncLauncher);
  function syncLauncher() {
    if (!els.launcher) return;
    var busy = state.streaming;
    var hiddenByDoor = doorOpen() && !state.open;
    els.launcher.setAttribute("data-door-open", hiddenByDoor ? "true" : "false");
    els.launcher.disabled = busy;
  }
  doorObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["style"] });
  doorObserver.observe(document.body, { attributes: true, attributeFilter: ["style"] });
  if (els.launcher) doorObserver.observe(els.launcher.parentNode, { attributes: true, subtree: true, attributeFilter: ["aria-expanded", "class"] });

  /* ---------- contextual Apply CTA (owner directive: CTAs only when the
     answer itself warrants one — a review/offer mention) ---------- */
  var ctaShown = false;
  function maybeShowApplyCta(replyText) {
    if (ctaShown) return;
    var triggers = ["free review", "apply", "review", "رایگان", "بررسی", "درخواست"];
    var hit = triggers.some(function (w) { return replyText.toLowerCase().indexOf(w) !== -1; });
    if (!hit) return;
    ctaShown = true;
    var a = document.createElement("a");
    a.className = "chat-apply-cta";
    a.href = locale === "fa" ? "/fa/apply/" : "/apply/";
    a.setAttribute("data-chat-cta", "apply");
    a.textContent = i18n.applyCta || "Apply for a free review";
    els.messages.appendChild(a);
    a.addEventListener("click", function () {
      track("chat_cta_clicked", { device: getDevice(), locale: locale, cta: "apply" });
      closeSheet();
    });
    scrollDown();
  }

  /* ---------- open/close (CSS transition driven via [data-open]) ---------- */
  function openSheet() {
    if (state.open) return;
    state.open = true;
    // Remove the no-JS hidden state; CSS drives visibility + transition.
    els.sheet.hidden = false;
    els.backdrop.hidden = false;
    // Double rAF so the browser paints the closed state before animating.
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        els.sheet.setAttribute("data-open", "true");
        els.backdrop.setAttribute("data-open", "true");
      });
    });
    els.launcher.setAttribute("aria-expanded", "true");
    // Owner directive 2026-09-05: the chat NEVER locks page scroll or
    // interaction - no overflow lock, no inert. The sheet is an overlay
    // the visitor can scroll the page under (backdrop taps still close).
    syncLauncher();
    setTimeout(function () { els.input && els.input.focus(); }, 120);
    track("chat_opened", { device: getDevice(), locale: locale });
  }
  function closeSheet() {
    if (!state.open) return;
    state.open = false;
    els.sheet.setAttribute("data-open", "false");
    els.backdrop.setAttribute("data-open", "false");
    els.launcher.setAttribute("aria-expanded", "false");
    syncLauncher();
    // After the transition ends, drop the sheet from the a11y tree fully.
    setTimeout(function () {
      if (!state.open) { els.sheet.hidden = true; els.backdrop.hidden = true; }
    }, 360);
    els.launcher.focus();
  }

  /* ---------- focus trap ---------- */
  els.sheet.addEventListener("keydown", function (e) {
    if (e.key !== "Tab") return;
    var focusables = els.sheet.querySelectorAll(
      'button, a[href], textarea, input, [tabindex]:not([tabindex="-1"])'
    );
    if (!focusables.length) return;
    var first = focusables[0];
    var last = focusables[focusables.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });

  /* ---------- messages ---------- */
  function scrollDown() {
    els.messages.scrollTop = els.messages.scrollHeight;
  }
  function addBubble(role, html) {
    var div = document.createElement("div");
    div.className = "chat-msg chat-msg-" + role;
    div.innerHTML = html;
    els.messages.appendChild(div);
    scrollDown();
    return div;
  }
  function addTyping() {
    var d = document.createElement("div");
    d.className = "chat-msg chat-msg-assistant chat-typing";
    d.innerHTML = '<span class="chat-dot"></span><span class="chat-dot"></span><span class="chat-dot"></span>';
    els.messages.appendChild(d);
    scrollDown();
    return d;
  }
  function showInlineError(msg) {
    var existing = document.getElementById("chat-inline-error");
    if (existing) existing.remove();
    var d = document.createElement("div");
    d.id = "chat-inline-error";
    d.className = "chat-msg chat-msg-error";
    d.innerHTML =
      "<p>" + escapeHtml(msg) + "</p>" +
      '<button type="button" class="chat-retry" data-chat-retry>' + escapeHtml(T("retry", "Retry")) + "</button>";
    els.messages.appendChild(d);
    scrollDown();
  }

  /* ---------- compact ask bar (sales-rep pattern, one time) ----------
     After the FIRST answer only: a one-line question from the assistant +
     a single-row form (name + email-or-phone). Never shown twice; never
     shown to returning visitors recognized by cookie. */
  function offerCaptureForm() {
    if (state.captureShown || state.captureDone || state.known) return;
    state.captureShown = true;
    // Rendered as an assistant bubble: same class as every answer so the
    // font size, padding, radius, and border match the conversation exactly.
    var bubble = document.createElement("div");
    bubble.className = "chat-msg chat-msg-assistant chat-ask";
    var form = document.createElement("form");
    form.id = "chat-ask-form";
    form.className = "chat-ask-form";
    form.innerHTML =
      '<label class="chat-ask-field"><span>' + escapeHtml(T("name", "Name")) + '</span><input name="name" type="text" required maxlength="80" placeholder="' + escapeHtml(T("namePh", "Name")) + '" autocomplete="name"></label>' +
      '<label class="chat-ask-field"><span>' + escapeHtml(T("contact", "Email or phone")) + '</span><input name="contact" type="text" required maxlength="254" placeholder="' + escapeHtml(T("contactPh", "Email or phone")) + '" autocomplete="email"></label>' +
      '<button type="submit" class="chat-ask-send">' + escapeHtml(T("sendContact", "Send")) + "</button>";
    bubble.innerHTML = '<p>' + escapeHtml(T("askTitle", "Can I ask who I\'m talking to — so a human on our side can get back to you fast?")) + '</p>';
    bubble.appendChild(form);
    els.messages.appendChild(bubble);
    scrollDown();
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var fd = new FormData(form);
      var name = String(fd.get("name") || "").trim();
      var contact = String(fd.get("contact") || "").trim();
      if (!name || !contact) return;
      // Parse the contact into email or phone for the cookie.
      var email = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(contact) ? contact.toLowerCase() : "";
      var phone = email ? "" : contact;
      state.known = { name: name, email: email || undefined, phone: phone || undefined };
      writeCookieContact(state.known);
      addBubble("user", escapeHtml(name + " — " + contact));
      bubble.remove(); form.remove();
      track("chat_handoff_email", { device: getDevice(), locale: locale });
      sendTurn(
        "Here are my contact details: name: " + name + "; " +
        (email ? "email: " + email : "phone: " + phone),
        { capture: true }
      );
    });
  }

  /* ---------- streaming turn ---------- */
  function sendTurn(text, opts) {
    opts = opts || {};
    if (state.streaming) return;
    if (!opts.capture) addBubble("user", escapeHtml(text));
    state.history.push({ role: "user", content: text });
    if (state.history.length > 16) state.history = state.history.slice(-16);
    state.turnCount++;
    track("chat_message_sent", { device: getDevice(), locale: locale, first: state.turnCount === 1 });

    state.streaming = true;
    syncLauncher();
    var typing = addTyping();
    var visible = "";   // reply text accumulated across the stream
    var completed = false; // set when the done frame is processed
    var abort = new AbortController();
    var abortTimer = setTimeout(function () { abort.abort(); }, 30000);

    var body = JSON.stringify({ messages: state.history, locale: locale, session_id: state.session, returning_visitor: state.known || undefined });

    // Bounded in-turn retry: providers burst-throttle (429/500); wait and
    // re-fetch inside the SAME turn so the typing indicator stays accurate.
    function fetchWithRetry(attempt) {
      return fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: body, signal: abort.signal })
        .then(function (res) {
          if ((res.status === 429 || res.status === 500) && attempt < 2) {
            return new Promise(function (resolve) { setTimeout(resolve, 2500); })
              .then(function () { return fetchWithRetry(attempt + 1); });
          }
          return res;
        });
    }

    fetchWithRetry(0)
      .then(function (res) {
        if (!res.ok) {
          return res.json().catch(function () { return {}; }).then(function (j) {
            throw new Error((j && j.error) || ("HTTP " + res.status));
          });
        }
        var reader = res.body.getReader();
        var dec = new TextDecoder();
        var buf = "";
        var bubble = null;
        function pump() {
          return reader.read().then(function (chunk) {
            if (completed) return;
            if (chunk.done) { clearTimeout(abortTimer); finishTurn(null); return; }
            buf += dec.decode(chunk.value, { stream: true });
            var parts = buf.split("\n\n");
            buf = parts.pop() || "";
            parts.forEach(function (frame) {
              var line = frame.trim();
              if (!line || line.indexOf("data:") !== 0) return;
              var payload;
              try { payload = JSON.parse(line.slice(5).trim()); } catch (e) { return; }
              if (payload.delta) {
                visible += payload.delta;
                if (!bubble) { typing.remove(); bubble = addBubble("assistant", ""); }
                bubble.innerHTML = renderRich(visible);
                scrollDown();
              } else if (payload.capture) {
                // CRM write already happened server-side; show the thanks.
                if (bubble) bubble.innerHTML = renderRich(visible + " " + payload.thanks_line);
                else { typing.remove(); bubble = addBubble("assistant", renderRich(payload.thanks_line || "")); }
                state.captureDone = true;
                // Remember the contact for future visits (cookie).
                if (state.known) writeCookieContact(state.known);
                else {
                  var kn = { name: "", email: "", phone: "" };
                  writeCookieContact(kn);
                }
                track("chat_lead_captured", { device: getDevice(), locale: locale, segment: payload.segment || "other" });
                scrollDown();
              } else if (payload.done) {
                completed = true;
                clearTimeout(abortTimer);
                if (payload.error) {
                  if (!bubble) { typing.remove(); addBubble("assistant", escapeHtml(T("errorLine", "Something went wrong on my side — try again in a moment."))); }
                  else { showInlineError(T("errorLine", "Something went wrong on my side — try again in a moment.")); }
                }
                try { reader.cancel(); } catch (e) {}
                finishTurn(null);
                return;
              }
            });
            return pump();
          });
        }
        return pump();
      })
      .catch(function (err) {
        clearTimeout(abortTimer);
        typing.remove();
        // A reply that already rendered must never be followed by an error
        // bubble (late stream noise is cosmetic, not a failure).
        if (!completed && !visible) showInlineError(T("errorLine", "Something went wrong on my side — try again in a moment."));
        else if (!completed) { /* reply rendered; absorb residual noise */ }
        finishTurn(err && !visible ? err : null);
      });

    function finishTurn(err) {
      state.streaming = false;
      syncLauncher();
      if (!err) {
        state.assistantReplies++;
        state.history.push({ role: "assistant", content: visible });
        if (state.history.length > 16) state.history = state.history.slice(-16);
        track("chat_message_reply", { device: getDevice(), locale: locale, chars: visible.length });
        maybeShowApplyCta(visible);
        // One-time compact ask after the FIRST answer; returning visitors
        // (cookie) are never asked again.
        if (state.assistantReplies === 1 && !state.captureDone && !state.known) offerCaptureForm();
      }
      els.input && els.input.focus();
    }
  }

  /* ---------- composer ---------- */
  els.composer.addEventListener("submit", function (e) {
    e.preventDefault();
    var text = els.input.value.trim();
    if (!text || state.streaming) return;
    els.input.value = "";
    autoGrow();
    els.send.disabled = true;
    if (els.suggestions) els.suggestions.classList.add("chat-suggestions-used");
    sendTurn(text);
  });
  function autoGrow() {
    els.input.style.height = "auto";
    els.input.style.height = Math.min(els.input.scrollHeight, 120) + "px";
    els.send.disabled = !els.input.value.trim() || state.streaming;
  }
  els.input.addEventListener("input", autoGrow);
  els.input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      els.composer.requestSubmit ? els.composer.requestSubmit() : els.composer.dispatchEvent(new Event("submit", { cancelable: true }));
    }
  });

  /* ---------- suggestions, CTAs, retry, nav links ---------- */
  els.messages.addEventListener("click", function (e) {
    var retry = e.target.closest("[data-chat-retry]");
    if (retry) {
      retry.closest(".chat-msg-error").remove();
      var last = state.history[state.history.length - 1];
      if (last && last.role === "user") {
        state.history.pop();
        sendTurn(last.content);
      }
      return;
    }
    var nav = e.target.closest("[data-chat-nav]");
    if (nav) {
      // Same-tab navigation; close the sheet so the target page is clean.
      closeSheet();
    }
  });

  /* ---------- Cal.com booking (same pattern as the site's data-cal-link) ---------- */
  function openCal() {
    if (typeof window.Cal === "function") {
      try { window.Cal("openForm", { url: "https://cal.com/" + (CTA.cal || "shayanspiel/15min").replace("cal:", "") }); return; } catch (e) {}
    }
    // Fallback: navigate to the Cal page in a new tab (function loader absent).
    window.open("https://cal.com/" + ((CTA.cal || "cal:shayanspiel/15min").replace("cal:", "")), "_blank", "noopener");
  }
  var calBtn = document.querySelector(".chat-cta-cal");
  if (calBtn) {
    calBtn.addEventListener("click", function () {
      track("chat_cta_clicked", { device: getDevice(), locale: locale, cta: "cal" });
      openCal();
    });
  }

  /* ---------- launcher wiring ---------- */
  els.launcher.addEventListener("click", function () {
    if (els.launcher.getAttribute("aria-expanded") === "true") closeSheet();
    else openSheet();
  });
  els.close.addEventListener("click", closeSheet);
  els.backdrop.addEventListener("click", closeSheet);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && state.open) closeSheet();
  });
  window.addEventListener("resize", autoGrow, { passive: true });

  syncLauncher();
})();
