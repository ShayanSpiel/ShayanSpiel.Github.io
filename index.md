---
layout: home
title: Shayan Spiel
description: Senior marketing leader turned AI engineer. 8+ years scaling Iran's biggest digital platforms. Now building agentic AI systems, content engines, and the GeoGent strategy game — writing in the open.
permalink: /
---

<section class="hero">
  <p class="muted small font-ui">Shayan Tawabi · <span class="nowrap">Tehran, Iran</span></p>
  <h1>Shayan Spiel</h1>
  <p class="lede">8+ years scaling Iran's biggest digital platforms — <strong>Digikala</strong>, <strong>Takhfifan</strong>, <strong>Varzesh3</strong>. 3M visitors in a single Black&nbsp;Friday campaign. 250k → 560k app installs in 2 seasons. <strong>Now:</strong> building agentic&nbsp;AI, content engines, and a strategy game. Writing in the open.</p>
  <p class="font-ui">
    <a href="/about/" class="plain"><strong>About</strong></a> ·&nbsp;
    <a href="https://twitter.com/ShayanSpiel" class="plain" target="_blank" rel="noopener noreferrer"><strong>X</strong></a> ·&nbsp;
    <a href="https://www.linkedin.com/in/shayayantawabi" class="plain" target="_blank" rel="noopener noreferrer"><strong>LinkedIn</strong></a> ·&nbsp;
    <a href="mailto:66shayan@gmail.com" class="plain"><strong>Email</strong></a>
  </p>
</section>

---

## Latest

{%- if site.posts.size > 0 -%}
  <ul class="list-plain">
    {%- for post in site.posts limit: 5 -%}
      <li>
        <a href="{{ post.url | relative_url }}" class="plain">
          <flex class="align-baseline">
            <span class="muted sr flex-shrink small mh nowrap font-ui">{{ post.date | date: "%b %-d, %Y" }}</span>
            <u>{{ post.title }}</u>
          </flex>
          {%- if post.description -%}
          <div class="small muted">{{ post.description | strip_html | truncatewords: 28 }}</div>
          {%- endif -%}
        </a>
      </li>
    {%- endfor -%}
  </ul>
  <p class="small"><a href="/posts/" class="plain">All posts →</a></p>
{%- else -%}
  <p class="muted small">New writing drops here soon. Subscribe below to get it in your inbox.</p>
{%- endif -%}

---

## Currently shipping

- **[GeoGent](/GeoGent-Waitlist/)** — a browser-based strategy MMO. Build cities, run economies, win wars. In the **test phase**. Waitlist open at [geogent.pages.dev](https://geogent.pages.dev).
- **The Spiel content engine** — the system that turns my dev sessions into social posts. 4 markdown files, $5/month, open in public. The first pillar post on this site is the spec.
- **5 productized services** — Audit, Framework, Build, Cohort, Workshop. Built for founders who want the second brain without building it themselves. See the [about page](/about/#what-i-offer).

---

## What this site is

A blog. A pillar-first blog. One substantial piece of writing per pillar. Every pillar yields 3 LinkedIn posts and 5–10 X posts that sample it. The blog carries the argument; the surfaces carry the conclusion. The atomized posts always link back to the source.

This is also the **front door** to my work. If you want the long version — the 8-year arc, the Iranian tech-platform credibility, the agentic-AI pivot, the offers — the [about page](/about/) has all of it.
