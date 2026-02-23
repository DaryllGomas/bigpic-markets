# Publishing a Supplementary Report

Step-by-step guide for publishing a new article to `research/supplementary/`.

---

## Directory Structure

```
research/supplementary/{PROJECT_DIR}/
├── {name}-thumb.jpg        # 1200x675 web thumbnail (committed)
├── {SOURCE}.png             # Full-res source image (NOT committed)
├── [article].html           # Self-contained article with inline CSS/JS
└── [PROJECT].md             # Internal project notes (committed)
```

---

## 1. Thumbnail

| Property   | Value                    |
|------------|--------------------------|
| Dimensions | **1200 x 675 px** (16:9) |
| Format     | JPG                      |
| Max size   | 200 KB                   |
| Naming     | `{name}-thumb.jpg`       |

Generate from a source PNG:
```bash
ffmpeg -i SOURCE.png -vf "scale=1200:675" -q:v 3 {name}-thumb.jpg
```

Do NOT commit full-resolution source images.

### Where thumbnails appear
1. Index page card (`<img class="card-thumb">`)
2. OG meta tags (`og:image`, `twitter:image`)
3. Social previews (X, iMessage, Slack, etc.)

---

## 2. OG & Twitter Meta Tags

Add to `<head>`:

```html
<meta name="description" content="[1-2 sentence summary]">
<meta property="og:title" content="[Article Title]">
<meta property="og:description" content="[1-2 sentence hook]">
<meta property="og:image" content="https://markets.bigpicsolutions.com/research/supplementary/{DIR}/{name}-thumb.jpg">
<meta property="og:url" content="https://markets.bigpicsolutions.com/research/supplementary/{DIR}/[filename].html">
<meta property="og:type" content="article">
<meta property="og:site_name" content="BigPic Solutions Research">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="[Article Title]">
<meta name="twitter:description" content="[1-2 sentence hook]">
<meta name="twitter:image" content="https://markets.bigpicsolutions.com/research/supplementary/{DIR}/{name}-thumb.jpg">
```

Base URL: `https://markets.bigpicsolutions.com`

---

## 3. Site Navigation

Add after `<body>`. Adapt `background` and `border-bottom` colors to the article palette:

| Palette       | Background                  | Border                              |
|---------------|-----------------------------|-------------------------------------|
| Parchment     | `rgba(26, 24, 18, 0.92)`   | `rgba(196, 154, 60, 0.08)`         |
| Dark          | `rgba(10, 15, 26, 0.92)`   | `rgba(232, 184, 125, 0.08)`        |
| Space / deep  | `rgba(6, 8, 13, 0.92)`     | `rgba(249, 115, 22, 0.08)`         |

```html
<nav class="bigpic-nav">
  <a href="../../../index.html" class="nav-brand">BigPic Solutions</a>
  <div class="nav-links">
    <div class="nav-dropdown">
      <a class="nav-link" href="#">Sectors &#9662;</a>
      <div class="nav-dropdown-menu">
        <a href="../../../research/ai/report.html">AI Infrastructure</a>
        <a href="../../../research/nuclear/report.html">Nuclear Energy</a>
        <a href="../../../research/space/report.html">Space</a>
        <a href="../../../research/quantum/report.html">Quantum Computing</a>
        <a href="../../../research/robotics/report.html">Robotics & Automation</a>
        <a href="../../../research/cybersecurity/report.html">Cybersecurity</a>
        <a href="../../../research/critical-minerals/report.html">Critical Minerals</a>
        <a href="../../../research/defense/report.html">Defense & Aerospace</a>
        <a href="../../../research/energy-storage/report.html">Energy Storage</a>
      </div>
    </div>
    <a class="nav-link" href="../../../eagle-eye/">Eagle Eye</a>
  </div>
</nav>
```

Rules:
- Dropdown label must say **"Sectors"** (not "Markets")
- Paths are relative from `research/supplementary/{DIR}/`
- Height: 52px, `z-index: 10000`

---

## 4. Share Dropdown

Place after `</nav>`. Position: `fixed; top: 4.2rem; right: 1.5rem; z-index: 9999`.

```html
<div class="share-wrapper">
  <button class="share-btn" onclick="toggleShare()" aria-label="Share this article">
    <svg viewBox="0 0 24 24"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>
    SHARE
  </button>
  <div class="share-dropdown" id="shareDropdown">
    <button class="share-option" onclick="copyLink()">
      <svg class="link-icon" viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
      Copy link
    </button>
    <a class="share-option" id="shareX" href="#" target="_blank" rel="noopener noreferrer" onclick="shareToX()">
      <svg class="x-logo" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
      Share on X
    </a>
    <div class="share-copied" id="shareCopied">Link copied!</div>
  </div>
</div>

<script>
const SHARE_URL = '[CANONICAL_URL]';
const SHARE_TEXT = '[ARTICLE_TITLE]. [OG_DESCRIPTION_HOOK]';

function toggleShare() {
  document.getElementById('shareDropdown').classList.toggle('open');
}
function copyLink() {
  navigator.clipboard.writeText(SHARE_URL).then(() => {
    const el = document.getElementById('shareCopied');
    el.classList.add('show');
    setTimeout(() => el.classList.remove('show'), 2000);
  });
}
function shareToX() {
  const url = 'https://x.com/intent/tweet?text=' + encodeURIComponent(SHARE_TEXT) + '&url=' + encodeURIComponent(SHARE_URL);
  document.getElementById('shareX').href = url;
}
document.addEventListener('click', (e) => {
  if (!e.target.closest('.share-wrapper')) {
    document.getElementById('shareDropdown').classList.remove('open');
  }
});
</script>
```

Adapt colors to article palette. **Critical:** include `.share-option svg { width: 15px; height: 15px; flex-shrink: 0; }` or icons render at full SVG size.

---

## 5. Index Page Card

Add to `index.html` at the **top** of the Supplementary Research `reports-grid` (newest first):

```html
<div class="report-card">
  <a href="research/supplementary/{DIR}/[filename].html">
    <img class="card-thumb" src="research/supplementary/{DIR}/{name}-thumb.jpg" alt="[Title]">
  </a>
  <div class="card-body">
    <span class="badge weekly">[Thesis|Analysis]</span>
    <div class="card-date">[Month Day, Year]</div>
    <h3>[Short Title]</h3>
    <p class="description">[1-2 sentence description]</p>
    <div class="links">
      <a href="research/supplementary/{DIR}/[filename].html">Interactive Report</a>
    </div>
  </div>
</div>
```

---

## 6. Commit & Deploy

```bash
git add research/supplementary/{DIR}/{article}.html \
       research/supplementary/{DIR}/{name}-thumb.jpg \
       index.html
# Do NOT commit full-res source images
git push origin main   # GitHub Pages deploys automatically
```

---

## 7. Verify

- [ ] Article loads at live URL
- [ ] Nav bar links work
- [ ] Share dropdown works (copy link + share to X)
- [ ] Index page shows card with thumbnail
- [ ] Social preview renders (test with X Card Validator)

---

## Published Articles

| Article | Directory | Date | Thumbnail |
|---------|-----------|------|-----------|
| Buy the Rumor, Sell the News | `Events-aapl-goog-nvda/` | Feb 23, 2026 | `events-thumb.jpg` |
| Rocket Lab — Flight Profile | `RocketLab/` | Feb 22, 2026 | `rklb-thumb.jpg` |
| NVDA Q4 FY2026 — Independent Analysis | `NVDA-q1-26/` | Feb 19, 2026 | `nvda-thumb.jpg` |
| Bits-to-Atoms | `Bit-Atoms/` | Feb 15, 2026 | `thumb.jpg` |
| The Middle Way — Palantir | `PLTR/` | Feb 14, 2026 | `PLTR-thumb.jpg` |
| SpaceX IPO | `SPACEX_IPO_THESIS/` | Feb 8, 2026 | `spacex-thumb.jpg` |
| Bubble & Logic — AI vs Dot-Com | `bubble-research/` | Feb 6, 2026 | `bubble-thumb.jpg` |
