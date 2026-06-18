---
layout: page
title: Sitemap
description: Every page and post on Shayan Spiel's site, listed for easy navigation and search engine discovery.
permalink: /sitemap/
sitemap: false
---

All blog posts, newest first:

<ul class="post-list">
{%- assign sorted = site.posts | sort: 'date' | reverse -%}
{%- for post in sorted -%}
  <li>
    <a href="{{ post.url | relative_url }}" class="plain post-list-link">
      <span class="post-list-date">{{ post.date | date: "%b %-d, %Y" }}</span>
      <span class="post-list-title">{{ post.title }}</span>
    </a>
  </li>
{%- endfor -%}
</ul>

Pages:

<ul>
  <li><a href="/">Home</a></li>
  <li><a href="/about/">About</a></li>
  <li><a href="/contact/">Contact</a></li>
  <li><a href="/posts/">All posts</a></li>
  <li><a href="/categories/">Topics</a></li>
  <li><a href="/tags/">Tags</a></li>
  <li><a href="/SpielEngine/">Spiel Engine — DFY Install</a></li>
  <li><a href="/GeoGent-Waitlist/">GeoGent — Alpha waitlist</a></li>
</ul>

Also available as <a href="/sitemap.xml">XML sitemap</a>.
