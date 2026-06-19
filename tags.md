---
layout: page
title: Tags
description: Browse blog posts by tag — content pipeline, Jekyll automation, AI agents, building in public, open-source writing tools, and developer content systems.
keywords: blog tags, all tags, content engine, automation, jekyll, agentic AI
image:
  path: /assets/og-default.png
  width: 1200
  height: 630
permalink: /tags/
---

<div class="ctn">
<article style="max-width:640px;margin:60px auto 0;padding:0">

<h1 style="margin-top:0">Tags</h1>

<div class="tag-cloud">
  {%- assign all_tags = site.posts | map: 'tags' | join: ',' | split: ',' | uniq | sort -%}
  {%- for tag in all_tags -%}
    {%- assign tag_strip = tag | strip -%}
    {%- if tag_strip != '' -%}
      <a href="/tags/#{{ tag_strip | slugify }}" class="plain tag-chip">#{{ tag_strip }}</a>
    {%- endif -%}
  {%- endfor -%}
</div>

<hr style="margin:32px 0">

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
            <li style="margin-bottom: 12px;">
              <a href="{{ post.url | relative_url }}" class="plain">
                <span class="muted small" style="display: inline-block; margin-right: 8px; font-family:var(--font-h);">{{ post.date | date: "%b %-d, %Y" }}</span>
                <u>{{ post.title }}</u>
              </a>
              {%- if post.description -%}
              <div class="small muted" style="margin-top: 4px;">{{ post.description | strip_html | truncatewords: 20 }}</div>
              {%- endif -%}
            </li>
          {%- endif -%}
        {%- endfor -%}
      </ul>
    </section>
  {%- endif -%}
{%- endfor -%}

</article>
</div>
