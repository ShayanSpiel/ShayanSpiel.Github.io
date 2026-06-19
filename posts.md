---
layout: blog
title: Blog
description: Every pillar post on the ShayanSpiel blog. Newest first.
keywords: all posts, blog archive, Shayan Spiel, session-as-content, content engine, building in public
image:
  path: /assets/og-default.png
  width: 1200
  height: 630
permalink: /posts/
---

{%- assign all_cats = site.posts | map: 'categories' | join: ',' | split: ',' | uniq | sort -%}

<nav class="blog-filters" id="post-filters" role="group" aria-label="Filter posts by category">
  <a href="/posts/" class="filter-btn active" data-filter="all" role="button" aria-pressed="true">
    All <span class="filter-count">{{ site.posts | size }}</span>
  </a>
  {%- for cat in all_cats -%}
    {%- assign cat_strip = cat | strip -%}
    {%- if cat_strip != '' -%}
      {%- assign cat_count = site.posts | where_exp: "p", "p.categories contains cat_strip" | size -%}
      <a href="?cat={{ cat_strip | slugify }}" class="filter-btn" data-filter="{{ cat_strip | slugify }}" role="button" aria-pressed="false">
        {{ cat_strip }} <span class="filter-count">{{ cat_count }}</span>
      </a>
    {%- endif -%}
  {%- endfor -%}
</nav>

<div id="post-list" class="blog-list">
  {%- assign sorted = site.posts | sort: 'date' | reverse -%}
  {%- for post in sorted -%}
    <a href="{{ post.url | relative_url }}" class="blog-row" data-categories="{%- for c in post.categories -%}{{ c | slugify }}{% unless forloop.last %} {% endunless %}{%- endfor -%}" data-tags="{%- for t in post.tags -%}{{ t | slugify }}{% unless forloop.last %} {% endunless %}{%- endfor -%}">
      <span class="blog-row-date">{{ post.date | date: "%b %-d, %Y" }}</span>
      <span class="blog-row-body">
        <span class="blog-row-title">{{ post.title }}</span>
        {%- if post.description -%}
        <span class="blog-row-desc">{{ post.description | strip_html | truncatewords: 18 }}</span>
        {%- endif -%}
      </span>
      <span class="blog-row-cat">{{ post.categories | first | default: 'Post' }}</span>
      <span class="blog-row-arrow" aria-hidden="true">&#8594;</span>
    </a>
  {%- endfor -%}
</div>

<div class="blog-load-more" id="load-more-wrap" style="display:none;">
  <button class="btn btn-ghost" id="load-more-btn" type="button">Load more posts</button>
</div>

<script>
(function(){
  var PAGE_SIZE = 10;
  var visibleCount = PAGE_SIZE;

  var params = new URLSearchParams(window.location.search);
  var cat = params.get('cat');
  var tag = params.get('tag');

  var allRows = document.querySelectorAll('.blog-row');
  var btns = document.querySelectorAll('.filter-btn');
  var loadMoreWrap = document.getElementById('load-more-wrap');
  var loadMoreBtn = document.getElementById('load-more-btn');

  function applyFilter() {
    if (!cat && !tag) return;
    if (cat) {
      btns.forEach(function(b){
        if (b.getAttribute('data-filter') === cat) {
          b.classList.add('active');
          b.setAttribute('aria-pressed', 'true');
        } else {
          b.classList.remove('active');
          b.setAttribute('aria-pressed', 'false');
        }
      });
      allRows.forEach(function(r){
        var cats = (r.getAttribute('data-categories') || '').split(' ');
        if (cats.indexOf(cat) >= 0) r.style.display = '';
        else r.style.display = 'none';
      });
    }
    if (tag) {
      allRows.forEach(function(r){
        var tags = (r.getAttribute('data-tags') || '').split(' ');
        if (tags.indexOf(tag) >= 0) r.style.display = '';
        else r.style.display = 'none';
      });
    }
  }

  function getVisibleRows() {
    var rows = [];
    allRows.forEach(function(r){
      if (r.style.display !== 'none') rows.push(r);
    });
    return rows;
  }

  function updateVisibility() {
    var visible = getVisibleRows();
    visible.forEach(function(r, i){
      if (i < visibleCount) r.style.display = '';
      else r.style.display = 'none';
    });
    if (visibleCount >= visible.length) {
      loadMoreWrap.style.display = 'none';
    } else {
      loadMoreWrap.style.display = '';
    }
  }

  applyFilter();
  updateVisibility();

  loadMoreBtn.addEventListener('click', function(){
    visibleCount += PAGE_SIZE;
    updateVisibility();
  });
})();
</script>
