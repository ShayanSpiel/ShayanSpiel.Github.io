---
layout: page
title: Topics
description: Browse blog posts by topic — AI agents, building in public, lead systems, content automation, and developer content pipeline methodology.
keywords: blog topics, categories, AI agents, building in public, lead systems, session-as-content
image:
  path: /assets/og-default.png
  width: 1200
  height: 630
permalink: /categories/
---

<p class="lede muted">Browse by topic. Each category groups posts around a core vertical.</p>

<div class="tag-cloud">
  {%- assign all_cats = site.posts | map: 'categories' | join: ',' | split: ',' | uniq | sort -%}
  {%- for cat in all_cats -%}
    {%- assign cat_strip = cat | strip -%}
    {%- if cat_strip != '' -%}
      <a href="/categories/#{{ cat_strip | slugify }}" class="plain tag-chip category-chip">{{ cat_strip }}</a>
    {%- endif -%}
  {%- endfor -%}
</div>

<hr>

{%- assign all_cats_sorted = site.posts | map: 'categories' | join: ',' | split: ',' | uniq | sort -%}
{%- for cat in all_cats_sorted -%}
  {%- assign cat_strip = cat | strip -%}
  {%- if cat_strip != '' -%}
    <section class="tag-section" id="{{ cat_strip | slugify }}">
      <h2 class="tag-section-title">
        <a href="/categories/#{{ cat_strip | slugify }}" class="plain">{{ cat_strip }}</a>
      </h2>
      <ul class="list-plain">
        {%- for post in site.posts -%}
          {%- if post.categories contains cat_strip -%}
            <li style="margin-bottom: 0.75rem;">
              <a href="{{ post.url | relative_url }}" class="plain">
                <span class="muted small" style="display: inline-block; margin-right: 0.5em;">{{ post.date | date: "%b %-d, %Y" }}</span>
                <u>{{ post.title }}</u>
              </a>
              {%- if post.description -%}
              <div class="small muted" style="margin-top: 0.15rem;">{{ post.description | strip_html | truncatewords: 28 }}</div>
              {%- endif -%}
            </li>
          {%- endif -%}
        {%- endfor -%}
      </ul>
    </section>
  {%- endif -%}
{%- endfor -%}
