---
layout: page
title: Topics
description: Browse blog posts by topic. Content pipeline for developers, AI systems, building in public, and the Spiel Engine.
keywords: blog topics, categories, content pipeline, AI systems, building in public, session-as-content
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
      {%- if cat_strip == 'Content Pipeline' -%}
        <p class="category-desc">How to turn build sessions into publishable content. The content pipeline for developers removes the identity switch between building and publishing. No blank pages. No editorial calendar. Just extraction.</p>
      {%- elsif cat_strip == 'AI Systems' -%}
        <p class="category-desc">State machines, agentic loops, and quality gates for AI content. Why prompts fail and loops survive. The architecture behind the Spiel Engine.</p>
      {%- elsif cat_strip == 'Building in Public' -%}
        <p class="category-desc">Your engineering decisions are already content. Positioning as infrastructure. The blog rebuild. Shipping in public without switching identities.</p>
      {%- elsif cat_strip == 'Spiel Engine' -%}
        <p class="category-desc">Product updates, feature ships, and architecture details. The open-source Session-as-Content Infrastructure for technical founders.</p>
      {%- endif -%}
      <ul class="list-plain">
        {%- for post in site.posts -%}
          {%- if post.categories contains cat_strip -%}
            <li>
              <a href="{{ post.url | relative_url }}" class="plain">
                <span class="muted small post-list-date">{{ post.date | date: "%b %-d, %Y" }}</span>
                <u>{{ post.title }}</u>
              </a>
              {%- if post.description -%}
              <div class="small muted post-list-desc">{{ post.description | strip_html | truncatewords: 28 }}</div>
              {%- endif -%}
            </li>
          {%- endif -%}
        {%- endfor -%}
      </ul>
    </section>
  {%- endif -%}
{%- endfor -%}
