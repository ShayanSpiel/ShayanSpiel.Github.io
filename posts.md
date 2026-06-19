---
layout: page
title: All posts
description: Browse all blog posts on the ShayanSpiel blog — AI content pipelines, Jekyll automation, build in public, agentic AI workflows, and developer content systems.
keywords: all posts, blog archive, Shayan Spiel, session-as-content, content engine, building in public
image:
  path: /assets/og-default.png
  width: 1200
  height: 630
permalink: /posts/
---

<div class="ctn">
<article style="max-width:640px;margin:60px auto 0;padding:0">

<h1 style="margin-top:0">All posts</h1>

<p class="lede muted">Every pillar post on the ShayanSpiel blog. Newest first.</p>

<p class="small">If a post is on this page, it is a pillar — a substantial piece of writing that produced 3 LinkedIn posts and 5–10 X posts. The blog carries the argument. The surfaces carry the conclusion.</p>

<p class="small">For the RSS feed, see <a href="/#subscribe">the footer</a>.</p>

</article>
</div>

<div class="ctn" style="margin-top:40px">
  <div class="grid-3" style="grid-template-columns:1fr">
    {%- assign sorted = site.posts | sort: 'date' | reverse -%}
    {%- for post in sorted -%}
      <a href="{{ post.url | relative_url }}" class="post-card" style="padding:20px 24px">
        <div class="post-card-date">{{ post.date | date: "%b %-d, %Y" }}</div>
        <div class="post-card-title">{{ post.title }}</div>
        {%- if post.description -%}
        <div class="post-card-excerpt">{{ post.description | strip_html | truncatewords: 28 }}</div>
        {%- endif -%}
      </a>
    {%- endfor -%}
  </div>
</div>
