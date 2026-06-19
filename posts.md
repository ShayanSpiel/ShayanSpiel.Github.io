---
layout: page
title: Blog
description: Browse all blog posts on the ShayanSpiel blog — AI content pipelines, Jekyll automation, build in public, agentic AI workflows, and developer content systems.
keywords: all posts, blog archive, Shayan Spiel, session-as-content, content engine, building in public
image:
  path: /assets/og-default.png
  width: 1200
  height: 630
permalink: /posts/
---

Every pillar post on the ShayanSpiel blog. Newest first.

{%- assign all_cats = site.posts | map: 'categories' | join: ',' | split: ',' | uniq | sort -%}

<div class="filters" id="post-filters">
  <a href="/posts/" class="filter-btn active" data-filter="all">
    All <span class="count">{{ site.posts | size }}</span>
  </a>
  {%- for cat in all_cats -%}
    {%- assign cat_strip = cat | strip -%}
    {%- if cat_strip != '' -%}
      {%- assign cat_count = site.posts | where_exp: "p", "p.categories contains cat_strip" | size -%}
      <a href="?cat={{ cat_strip | slugify }}" class="filter-btn" data-filter="{{ cat_strip | slugify }}">
        {{ cat_strip }} <span class="count">{{ cat_count }}</span>
      </a>
    {%- endif -%}
  {%- endfor -%}
</div>

<div id="post-list" class="grid grid-3">
  {%- assign sorted = site.posts | sort: 'date' | reverse -%}
  {%- for post in sorted -%}
    <a href="{{ post.url | relative_url }}" class="post-card" data-categories="{%- for c in post.categories -%}{{ c | slugify }}{% unless forloop.last %} {% endunless %}{%- endfor -%}">
      <div class="post-card-date">{{ post.date | date: "%b %-d, %Y" }}</div>
      <h3 class="post-card-title">{{ post.title }}</h3>
      {%- if post.description -%}
      <p class="post-card-excerpt">{{ post.description | strip_html | truncatewords: 22 }}</p>
      {%- endif -%}
      <div class="post-card-cat">{{ post.categories | first | default: 'Post' }}</div>
    </a>
  {%- endfor -%}
</div>

<script>
(function(){
  var params = new URLSearchParams(window.location.search);
  var cat = params.get('cat');
  if(!cat) return;
  var btns = document.querySelectorAll('.filter-btn');
  var cards = document.querySelectorAll('.post-card');
  btns.forEach(function(b){
    if(b.getAttribute('data-filter') === cat) b.classList.add('active');
    else b.classList.remove('active');
  });
  cards.forEach(function(c){
    var cats = (c.getAttribute('data-categories') || '').split(' ');
    if(cats.indexOf(cat) >= 0) c.style.display = '';
    else c.style.display = 'none';
  });
})();
</script>
