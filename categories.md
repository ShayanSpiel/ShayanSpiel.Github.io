---
layout: page
title: Categories
description: Browse all posts by category.
permalink: /categories/
---

<p class="lede muted">Browse all posts by category. Click any category to jump to its posts below.</p>

<div class="tag-cloud font-ui">
  {%- assign all_cats = site.posts | map: 'categories' | join: ',' | split: ',' | uniq | sort -%}
  {%- for cat in all_cats -%}
    {%- assign cat_strip = cat | strip -%}
    {%- if cat_strip != '' -%}
      <a href="#{{ cat_strip | slugify }}" class="plain tag-chip category-chip">{{ cat_strip }}</a>
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
        <a href="#{{ cat_strip | slugify }}" class="plain">{{ cat_strip }}</a>
      </h2>
      <ul class="list-plain">
        {%- for post in site.posts -%}
          {%- if post.categories contains cat_strip -%}
            <li>
              <a href="{{ post.url | relative_url }}" class="plain">
                <flex class="align-baseline">
                  <span class="muted small font-ui nowrap">{{ post.date | date: "%b %-d, %Y" }}</span>
                  <u>{{ post.title }}</u>
                </flex>
                {%- if post.description -%}
                <div class="small muted">{{ post.description | strip_html | truncatewords: 28 }}</div>
                {%- endif -%}
              </a>
            </li>
          {%- endif -%}
        {%- endfor -%}
      </ul>
    </section>
  {%- endif -%}
{%- endfor -%}
