---
layout: page
title: Tags
description: Browse blog posts by tag — content pipeline, Jekyll automation, AI agents, building in public, open-source writing tools, and developer content systems.
keywords: blog tags, all tags, content engine, automation, jekyll, agentic AI
image: /assets/og-default.png
permalink: /tags/
---

<div class="tag-cloud font-ui">
  {%- assign all_tags = site.posts | map: 'tags' | join: ',' | split: ',' | uniq | sort -%}
  {%- for tag in all_tags -%}
    {%- assign tag_strip = tag | strip -%}
    {%- if tag_strip != '' -%}
      <a href="/tags/#{{ tag_strip | slugify }}" class="plain tag-chip">#{{ tag_strip }}</a>
    {%- endif -%}
  {%- endfor -%}
</div>

<hr>

{%- assign all_tags_sorted = site.posts | map: 'tags' | join: ',' | split: ',' | uniq | sort -%}
{%- for tag in all_tags_sorted -%}
  {%- assign tag_strip = tag | strip -%}
  {%- if tag_strip != '' -%}
    <section class="tag-section" id="{{ tag_strip | slugify }}">
      <h2 class="tag-section-title">
        <a href="/tags/#{{ tag_strip | slugify }}" class="plain">#{{ tag_strip }}</a>
      </h2>
      <ul class="list-plain">
        {%- for post in site.posts -%}
          {%- if post.tags contains tag_strip -%}
            <li style="margin-bottom: 0.75rem;">
              <a href="{{ post.url | relative_url }}" class="plain">
                <span class="muted small font-ui" style="display: inline-block; margin-right: 0.5em;">{{ post.date | date: "%b %-d, %Y" }}</span>
                <u>{{ post.title }}</u>
              </a>
              {%- if post.description -%}
              <div class="small muted" style="margin-top: 0.15rem;">{{ post.description | strip_html | truncatewords: 20 }}</div>
              {%- endif -%}
            </li>
          {%- endif -%}
        {%- endfor -%}
      </ul>
    </section>
  {%- endif -%}
{%- endfor -%}
