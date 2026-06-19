---
layout: page
title: Sitemap
description: Every page and post on Shayan Spiel's site, listed for easy navigation and search engine discovery.
permalink: /sitemap/
sitemap: false
---

All blog posts, newest first:

<div class="grid" style="grid-template-columns: 1fr; gap: 0; margin-top: var(--s-5);">
  {%- assign sorted = site.posts | sort: 'date' | reverse -%}
  {%- for post in sorted -%}
    <a href="{{ post.url | relative_url }}" class="post-list-link">
      <span class="post-list-date">{{ post.date | date: "%b %-d, %Y" }}</span>
      <span class="post-list-title">{{ post.title }}</span>
    </a>
  {%- endfor -%}
</div>

<hr class="divider">

## Pages

- [Home](/)
- [About](/about/)
- [Contact](/contact/)
- [All posts](/posts/)
- [Topics](/categories/)
- [Tags](/tags/)
- [Spiel Engine — DFY Install](/SpielEngine/)
- [GeoGent — Alpha waitlist](/GeoGent-Waitlist/)

Also available as [XML sitemap](/sitemap.xml).
