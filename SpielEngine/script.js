/* =====================================================================
   Spiel Engine — Landing Page Interactions
   ===================================================================== */

/* ---- Copy to clipboard ---- */
function setupCopy(boxId, btnId) {
  var box = document.getElementById(boxId);
  var btn = document.getElementById(btnId);
  if (!box || !btn) return;
  function cp() {
    try { navigator.clipboard.writeText('brew install ShayanSpiel/spiel/spiel'); }
    catch(e) { var t=document.createElement('textarea'); t.value='brew install ShayanSpiel/spiel/spiel'; document.body.appendChild(t); t.select(); document.execCommand('copy'); document.body.removeChild(t); }
    box.classList.add('copied');
    setTimeout(function(){ box.classList.remove('copied'); }, 2200);
  }
  box.addEventListener('click', cp);
}
setupCopy('hero-cli','hero-btn');
setupCopy('cli2','btn2');

/* ---- Terminal animation ---- */
var termBody = document.getElementById('term-body');
var termStarted = false;

function runTerminal() {
  if (termStarted) return;
  termStarted = true;

  var promptLine = document.createElement('div');
  promptLine.className = 't-line show';
  promptLine.innerHTML = '<span class="prompt">$</span> <span class="cmd-text" id="typed-cmd"></span><span class="cursor-blink"></span>';
  termBody.appendChild(promptLine);

  var cmdText = '/post';
  var charIdx = 0;
  function typeChar() {
    if (charIdx < cmdText.length) {
      document.getElementById('typed-cmd').textContent += cmdText[charIdx];
      charIdx++;
      setTimeout(typeChar, 80 + Math.random() * 40);
    } else {
      setTimeout(function() {
        var cursor = promptLine.querySelector('.cursor-blink');
        if (cursor) cursor.remove();
        document.getElementById('typed-cmd').textContent = cmdText;
        runSteps();
      }, 400);
    }
  }
  setTimeout(typeChar, 500);
}

function runSteps() {
  var steps = [
    { type: 'loading', msg: '> Loading skills from .spiel/skills' },
    { type: 'check', msg: 'LOADING SKILL/SCRIPTS' },
    { type: 'loading', msg: '> Scanning session context' },
    { type: 'check', msg: 'SESSION_CAPTURE' },
    { type: 'loading', msg: '> Running ICP simulation' },
    { type: 'check', msg: 'COMPILE (ICP World)' },
    { type: 'loading', msg: '> Selecting format wizard' },
    { type: 'check', msg: 'SELECT FORMAT_WIZARD' },
    { type: 'loading', msg: '> Drafting content in your voice' },
    { type: 'check', msg: 'DRAFTING' },
    { type: 'loading', msg: '> Generating banner' },
    { type: 'check', msg: 'BANNER_GENERATING' },
    { type: 'sep' },
    { type: 'text', msg: 'Publishing to:', cls: 'highlight' },
    { type: 'text', msg: '  \u2713 X / Twitter', cls: 'white' },
    { type: 'text', msg: '  \u2713 LinkedIn', cls: 'white' },
    { type: 'text', msg: '  \u2713 Threads', cls: 'white' },
    { type: 'text', msg: '  \u2713 Mastodon', cls: 'white' },
    { type: 'text', msg: '  \u2713 Bluesky', cls: 'white' },
    { type: 'text', msg: '  \u2713 Blog', cls: 'white' },
    { type: 'sep' },
    { type: 'check', msg: 'DONE \u2014 6 platforms published' },
    { type: 'text', msg: '> Banner saved \u2192 ./banners/session-01.png', cls: 'dim' },
    { type: 'text', msg: '> Draft saved \u2192 ./drafts/session-01.md', cls: 'dim' },
    { type: 'text', msg: 'Session captured. Content created. Published.', cls: 'highlight' }
  ];

  var i = 0;
  function nextStep() {
    if (i >= steps.length) return;
    var item = steps[i];
    i++;

    if (item.type === 'sep') {
      var sep = document.createElement('div');
      sep.className = 't-sep';
      termBody.appendChild(sep);
      requestAnimationFrame(function(){ sep.classList.add('show'); });
      termBody.scrollTop = termBody.scrollHeight;
      setTimeout(nextStep, 200);
      return;
    }

    if (item.type === 'loading') {
      var el = document.createElement('div');
      el.className = 't-line';
      el.innerHTML = '<span class="msg dim">' + item.msg + '</span><span class="msg dim" id="dot-anim"></span>';
      termBody.appendChild(el);
      requestAnimationFrame(function(){ el.classList.add('show'); });
      termBody.scrollTop = termBody.scrollHeight;

      var dotEl = el.querySelector('#dot-anim');
      var dots = 0;
      var dotTimer = setInterval(function() {
        dots++;
        dotEl.textContent = '.'.repeat(dots);
        if (dots >= 3) {
          clearInterval(dotTimer);
          setTimeout(nextStep, 300);
        }
      }, 150);
      return;
    }

    var el = document.createElement('div');
    el.className = 't-line';
    if (item.type === 'check') {
      el.innerHTML = '<span class="check">\u2713</span> <span class="msg highlight">' + item.msg + '</span>';
    } else {
      el.innerHTML = '<span class="msg ' + item.cls + '">' + item.msg + '</span>';
    }
    termBody.appendChild(el);
    requestAnimationFrame(function(){ el.classList.add('show'); });
    termBody.scrollTop = termBody.scrollHeight;
    setTimeout(nextStep, item.type === 'check' ? 150 : 200);
  }

  nextStep();
}

/* ---- Intersection Observer: Terminal ---- */
var termObs = new IntersectionObserver(function(entries) {
  entries.forEach(function(e){ if (e.isIntersecting) { runTerminal(); termObs.disconnect(); } });
}, { threshold: 0.3 });
var termSection = document.querySelector('.terminal-section');
if (termSection) termObs.observe(termSection);

/* ---- Intersection Observer: Publish transition ---- */
var pubTrans = document.getElementById('pub-transition');
var xPost = document.getElementById('x-post');
var pubObs = new IntersectionObserver(function(entries) {
  entries.forEach(function(e){
    if (e.isIntersecting) {
      pubTrans.classList.add('show');
      pubObs.disconnect();
      watchTweetLoad();
    }
  });
}, { threshold: 0.2 });
if (pubTrans) pubObs.observe(pubTrans);

/* ---- X Tweet embed: fetch oembed with dark theme ---- */
function watchTweetLoad() {
  if (!xPost) return;
  var container = document.getElementById('x-embed-container');
  if (!container) return;

  var tweetUrl = 'https://x.com/ShayanSpiel/status/2067446487005466949';
  var oembedUrl = 'https://publish.twitter.com/oembed?url=' + encodeURIComponent(tweetUrl) + '&theme=dark&omit_script=true';

  fetch(oembedUrl)
    .then(function(r) { return r.json(); })
    .then(function(data) {
      container.innerHTML = data.html;
      var script = document.createElement('script');
      script.src = 'https://platform.x.com/widgets.js';
      script.charset = 'utf-8';
      script.async = true;
      script.onload = function() { xPost.classList.add('show'); };
      document.body.appendChild(script);
      setTimeout(function() { xPost.classList.add('show'); }, 4000);
    })
    .catch(function() {
      xPost.classList.add('show');
    });
}

/* ---- Cycle words animation ---- */
var cycleWords = ['[Topic]', '[Bug Fix]', '[Feature]', '[Architecture]', '[Lesson]'];
var cycleIdx = 0;
var cycleEl = document.getElementById('cycle-word');
setInterval(function() {
  cycleEl.style.opacity = '0';
  cycleEl.style.transform = 'translateY(-6px)';
  setTimeout(function() {
    cycleIdx = (cycleIdx + 1) % cycleWords.length;
    cycleEl.textContent = cycleWords[cycleIdx];
    cycleEl.style.transform = 'translateY(6px)';
    requestAnimationFrame(function() {
      cycleEl.style.transition = 'all .3s ease';
      cycleEl.style.opacity = '1';
      cycleEl.style.transform = 'translateY(0)';
    });
  }, 250);
}, 2200);

/* ---- Scroll reveal ---- */
var revealObs = new IntersectionObserver(function(entries) {
  entries.forEach(function(e){ if (e.isIntersecting) { e.target.classList.add('visible'); } });
}, { threshold: 0.1 });
document.querySelectorAll('.reveal').forEach(function(el){ revealObs.observe(el); });

/* ---- Nav hide on scroll down ---- */
(function(){
  var nav = document.querySelector('.se-nav');
  if (!nav) return;
  var lastY = 0;
  window.addEventListener('scroll', function(){
    var y = window.scrollY;
    if (y > 80 && y > lastY) { nav.classList.add('nav-hidden'); }
    else { nav.classList.remove('nav-hidden'); }
    lastY = y;
  }, {passive: true});
})();

/* ---- FAQ accordion ---- */
document.querySelectorAll('.faq-q').forEach(function(btn) {
  btn.addEventListener('click', function() {
    var card = this.closest('.faq-card');
    var wasOpen = card.classList.contains('open');
    document.querySelectorAll('.faq-card.open').forEach(function(el){
      el.classList.remove('open');
      el.querySelector('.faq-q').setAttribute('aria-expanded', 'false');
    });
    if (!wasOpen) {
      card.classList.add('open');
      this.setAttribute('aria-expanded', 'true');
    }
  });
});
