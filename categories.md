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

Browse by topic. Each category groups posts around a core vertical.

<div class="tag-cloud">
  {%- assign all_cats = site.posts | map: 'categories' | join: ',' | split: ',' | uniq | sort -%}
  {%- for cat in all_cats -%}
    {%- assign cat_strip = cat | strip -%}
    {%- if cat_strip != '' -%}
      <a href="/posts/?cat={{ cat_strip | slugify }}" class="tag-chip">{{ cat_strip }}</a>
    {%- endif -%}
  {%- endfor -%}
</div>

<hr class="divider">

{%- assign all_cats_sorted = site.posts | map: 'categories' | join: ',' | split: ',' | uniq | sort -%}
{%- for cat in all_cats_sorted -%}
  {%- assign cat_strip = cat | strip -%}
  {%- if cat_strip != '' -%}
    <section id="{{ cat_strip | slugify }}">
      <h2><a href="/posts/?cat={{ cat_strip | slugify }}" class="plain">{{ cat_strip }}</a></h2>
      <ul class="list-plain">
        {%- for post in site.posts -%}
          {%- if post.categories contains cat_strip -%}
            <li>
              <a href="{{ post.url | relative_url }}" class="plain">
                <span class="muted small" style="display: inline-block; margin-right: var(--s-3); font-family: var(--f-h);">{{ post.date | date: "%b %-d, %Y" }}</span>
                <u>{{ post.title }}</u>
              </a>
              {%- if post.description -%}
              <div class="small muted" style="margin-top: 4px;">{{ post.description | strip_html | truncatewords: 28 }}</div>
              {%- endif -%}
            </li>
          {%- endif -%}
        {%- endfor -%}
      </ul>
    </section>
  {%- endif -%}
{%- endfor -%}
