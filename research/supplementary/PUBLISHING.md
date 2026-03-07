# Publishing a Supplementary Report

Step-by-step guide for publishing a new article to `research/supplementary/`.

**Repo:** `/home/spicymeatball/projects/bigpic-markets/`
**Live URL:** `https://markets.bigpicsolutions.com/`
**Deploy:** GitHub Pages — push to `main` = live in seconds.

---

## Prerequisites

The HTML report should already exist — either built by `/report` or carried over from the Capital research folder. The source thumbnail image (PNG) should be in the same directory as the HTML.

**Source location (Capital research):** `~/Google-Drive/BigPic - Capital/Research/...`
**Publish location (repo):** `~/projects/bigpic-markets/research/supplementary/{DIR}/`

---

## Quick Reference — Full Publish Sequence

```bash
# All commands run from ~/projects/bigpic-markets/

# 1. Create directory
mkdir -p research/supplementary/{DIR}

# 2. Copy HTML
cp "SOURCE_PATH/{article}.html" research/supplementary/{DIR}/{article}.html

# 3. Generate thumbnail (1200x675, under 200KB)
ffmpeg -y -i "SOURCE_PATH/{SOURCE}.png" -vf "scale=1200:675" -q:v 5 research/supplementary/{DIR}/{name}-thumb.jpg

# 4. Edit the HTML — add OG meta tags, nav CSS, nav bar, share dropdown (see sections below)

# 5. Edit index.html — add card at top of Supplementary Research grid

# 6. Commit and deploy
git add research/supplementary/{DIR}/{article}.html \
       research/supplementary/{DIR}/{name}-thumb.jpg \
       index.html
git commit -m "Publish {Article Title}"
git push origin main
```

Do NOT commit full-resolution source images (PNG). Only commit the HTML and thumb JPG.

---

## Directory Structure

```
research/supplementary/{PROJECT_DIR}/
├── {article}.html          # Self-contained article with inline CSS/JS (committed)
├── {name}-thumb.jpg        # 1200x675 web thumbnail (committed)
├── {SOURCE}.png            # Full-res source image (NOT committed)
└── [notes].md              # Internal project notes (optional, committed)
```

---

## Step 1: Thumbnail

| Property   | Value                    |
|------------|--------------------------|
| Dimensions | **1200 x 675 px** (16:9) |
| Format     | JPG                      |
| Max size   | 200 KB                   |
| Naming     | `{name}-thumb.jpg`       |

```bash
ffmpeg -y -i SOURCE.png -vf "scale=1200:675" -q:v 5 {name}-thumb.jpg
```

If over 200KB at `-q:v 5`, increase to `-q:v 6` or `-q:v 7`. If under 150KB at `-q:v 5`, try `-q:v 3` for better quality.

### Where thumbnails appear
1. Index page card (`<img class="card-thumb">`)
2. OG meta tags (`og:image`, `twitter:image`)
3. Social previews (X, iMessage, Slack, etc.)

---

## Step 2: OG & Twitter Meta Tags

Insert into `<head>`, after `<title>`:

```html
<meta name="description" content="[1-2 sentence summary]">
<meta property="og:title" content="[Article Title]">
<meta property="og:description" content="[1-2 sentence hook]">
<meta property="og:image" content="https://markets.bigpicsolutions.com/research/supplementary/{DIR}/{name}-thumb.jpg">
<meta property="og:url" content="https://markets.bigpicsolutions.com/research/supplementary/{DIR}/{article}.html">
<meta property="og:type" content="article">
<meta property="og:site_name" content="BigPic Solutions Research">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="[Article Title]">
<meta name="twitter:description" content="[1-2 sentence hook]">
<meta name="twitter:image" content="https://markets.bigpicsolutions.com/research/supplementary/{DIR}/{name}-thumb.jpg">
```

---

## Step 3: Nav Bar + Share Dropdown CSS

Insert before `</style>`. Adapt colors to match the article's palette:

| Palette       | Nav Background              | Nav Border                          | Brand Gradient                              |
|---------------|-----------------------------|-------------------------------------|---------------------------------------------|
| Dark (default)| `rgba(10, 15, 26, 0.92)`   | `rgba(245, 158, 11, 0.08)`         | `linear-gradient(135deg, #e2e8f0, #f59e0b)` |
| Parchment     | `rgba(26, 24, 18, 0.92)`   | `rgba(196, 154, 60, 0.08)`         | `linear-gradient(135deg, #fdf6ec, #e8b87d)` |
| Space / deep  | `rgba(6, 8, 13, 0.92)`     | `rgba(249, 115, 22, 0.08)`         | `linear-gradient(135deg, #e2e8f0, #f97316)` |

```css
/* === SITE NAV === */
.bigpic-nav{position:fixed;top:0;left:0;right:0;z-index:10000;background:rgba(10,15,26,0.92);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid rgba(245,158,11,0.08);display:flex;align-items:center;padding:0 1.5rem;height:52px}
.bigpic-nav a{text-decoration:none}
.bigpic-nav .nav-brand{font-weight:700;font-size:1rem;background:linear-gradient(135deg,#e2e8f0,#f59e0b);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-right:32px}
.bigpic-nav .nav-links{display:flex;align-items:center;gap:4px}
.bigpic-nav .nav-link{color:#94a3b8;font-size:0.82rem;font-weight:500;padding:6px 12px;border-radius:6px;transition:0.2s ease}
.bigpic-nav .nav-link:hover{color:#e2e8f0;background:rgba(255,255,255,0.05)}
.bigpic-nav .nav-dropdown{position:relative}
.bigpic-nav .nav-dropdown-menu{display:none;position:absolute;top:100%;left:0;background:rgba(10,15,26,0.96);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:6px;min-width:180px;box-shadow:0 8px 32px rgba(0,0,0,0.4)}
.bigpic-nav .nav-dropdown:hover .nav-dropdown-menu{display:block}
.bigpic-nav .nav-dropdown-menu a{display:block;color:#94a3b8;font-size:0.82rem;padding:8px 12px;border-radius:6px;transition:0.2s ease}
.bigpic-nav .nav-dropdown-menu a:hover{color:#e2e8f0;background:rgba(255,255,255,0.05)}
@media(max-width:600px){.bigpic-nav .nav-links{display:none}}

/* === SHARE DROPDOWN === */
.share-wrapper{position:fixed;top:4.2rem;right:1.5rem;z-index:9999}
.share-btn{display:flex;align-items:center;gap:0.5rem;padding:0.55rem 1rem;background:rgba(10,15,26,0.85);border:1px solid rgba(255,255,255,0.08);border-radius:8px;color:#94a3b8;font-size:0.78rem;font-weight:600;font-family:'Inter',sans-serif;letter-spacing:0.06em;cursor:pointer;backdrop-filter:blur(10px);transition:0.2s ease}
.share-btn:hover{color:#e2e8f0;border-color:rgba(245,158,11,0.3)}
.share-btn svg{width:14px;height:14px;stroke:#94a3b8;stroke-width:2;fill:none;stroke-linecap:round;stroke-linejoin:round;transition:0.2s ease}
.share-btn:hover svg{stroke:#f59e0b}
.share-dropdown{display:none;position:absolute;top:calc(100% + 6px);right:0;background:rgba(10,15,26,0.96);border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:6px;min-width:160px;box-shadow:0 8px 32px rgba(0,0,0,0.4)}
.share-dropdown.open{display:block}
.share-option{display:flex;align-items:center;gap:8px;width:100%;padding:8px 12px;background:none;border:none;color:#94a3b8;font-size:0.82rem;font-family:'Inter',sans-serif;cursor:pointer;border-radius:6px;transition:0.2s ease;text-decoration:none}
.share-option:hover{color:#e2e8f0;background:rgba(255,255,255,0.05)}
.share-option svg{width:15px;height:15px;flex-shrink:0}
.link-icon{stroke:#94a3b8;stroke-width:2;fill:none;stroke-linecap:round;stroke-linejoin:round}
.x-logo{fill:#94a3b8}
.share-option:hover .link-icon{stroke:#f59e0b}
.share-option:hover .x-logo{fill:#f59e0b}
.share-copied{display:none;padding:8px 12px;color:#10b981;font-size:0.8rem;text-align:center}
.share-copied.show{display:block}
```

**Adapt accent color:** Replace `#f59e0b` (amber) with the article's accent color throughout if needed.

---

## Step 4: Nav Bar + Share Dropdown HTML

Insert after `<body>`, before the first `<section>`:

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
const SHARE_URL = 'https://markets.bigpicsolutions.com/research/supplementary/{DIR}/{article}.html';
const SHARE_TEXT = '[Article Title]. [1-2 sentence hook]';

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

**Replace placeholders:** `{DIR}`, `{article}`, `[Article Title]`, `[1-2 sentence hook]`.

Rules:
- Dropdown label must say **"Sectors"** (not "Markets")
- Paths are relative from `research/supplementary/{DIR}/`
- Nav height: 52px, `z-index: 10000`
- Share button: `z-index: 9999`, positioned below nav

---

## Step 5: Index Page Card

Add to `index.html` at the **top** of the Supplementary Research `reports-grid` (newest first):

```html
<div class="report-card">
  <a href="research/supplementary/{DIR}/{article}.html">
    <img class="card-thumb" src="research/supplementary/{DIR}/{name}-thumb.jpg" alt="[Title]">
  </a>
  <div class="card-body">
    <span class="badge weekly">[Thesis|Analysis]</span>
    <div class="card-date">[Month Day, Year]</div>
    <h3>[Short Title]</h3>
    <p class="description">[1-2 sentence description]</p>
    <div class="links">
      <a href="research/supplementary/{DIR}/{article}.html">Interactive Report</a>
    </div>
  </div>
</div>
```

---

## Step 6: Commit & Deploy

```bash
cd ~/projects/bigpic-markets

git add research/supplementary/{DIR}/{article}.html \
       research/supplementary/{DIR}/{name}-thumb.jpg \
       index.html

git commit -m "Publish {Article Title}"
git push origin main   # GitHub Pages deploys automatically
```

---

## Step 7: Verify

- [ ] Article loads at `https://markets.bigpicsolutions.com/research/supplementary/{DIR}/{article}.html`
- [ ] Nav bar links work (sector dropdown, Eagle Eye)
- [ ] Share dropdown works (copy link + share to X)
- [ ] Index page shows card with thumbnail at top of Supplementary grid
- [ ] Social preview renders (test with [X Card Validator](https://cards-dev.twitter.com/validator))

---

---

## Hot Takes

Hot Takes are quick-hit teardowns and contrarian calls. Same publish pipeline as Supplementary Research with two differences:

1. **Repo path:** `research/hot-takes/{SLUG}/` instead of `research/supplementary/{SLUG}/`
2. **No internal report nav:** Hot Takes reports do NOT include the decorative internal `<nav>` (Big Pic Solutions logo + Home/Technology/Markets/About Me links). The site nav bar is sufficient.

### Quick Reference — Hot Takes Sequence

```bash
# 1. Create directory
mkdir -p research/hot-takes/{SLUG}

# 2. Copy HTML (omit or remove internal nav block if present)
cp "SOURCE_PATH/{article}.html" research/hot-takes/{SLUG}/{article}.html

# 3. Generate thumbnail
ffmpeg -y -i "SOURCE_PATH/{SOURCE}.png" -vf "scale=1200:675" -q:v 5 research/hot-takes/{SLUG}/{name}-thumb.jpg

# 4. Add OG meta tags, nav CSS, site nav bar, share dropdown (same as Supplementary — see above)
#    Nav paths: ../../../index.html (3 levels up)

# 5. Add card to index.html — Hot Takes section (badge: "Teardown" or "Hot Take")

# 6. Commit and deploy
git add research/hot-takes/{SLUG}/{article}.html \
       research/hot-takes/{SLUG}/{name}-thumb.jpg \
       index.html
git commit -m "Publish Hot Take: {Title}"
git push origin main
```

### Published Hot Takes

| Article | Directory | Date | Thumbnail |
|---------|-----------|------|-----------|
| Short IGV, Long PLTR: Teardown | `Short-IGV-Long-PLTR/` | 2026-03-07 | `trade-thesis-teardown-thumb.jpg` |

---

## Published Articles

| Article | Directory | Date | Thumbnail |
|---------|-----------|------|-----------|
| The SaaSpocalypse Is Overdone | `SaaSpocalypse/` | Feb 26, 2026 | `saaspocalypse-thumb.jpg` |
| The Crash, the Transition, and the Golden Age | `Citrini/` | Feb 23, 2026 | `citrini-thumb.jpg` |
| Buy the Rumor, Sell the News | `Events-aapl-goog-nvda/` | Feb 23, 2026 | `events-thumb.jpg` |
| Rocket Lab — Flight Profile | `RocketLab/` | Feb 22, 2026 | `rklb-thumb.jpg` |
| NVDA Q4 FY2026 — Independent Analysis | `NVDA-q1-26/` | Feb 19, 2026 | `nvda-thumb.jpg` |
| Bits-to-Atoms | `Bit-Atoms/` | Feb 15, 2026 | `thumb.jpg` |
| The Middle Way — Palantir | `PLTR/` | Feb 14, 2026 | `PLTR-thumb.jpg` |
| SpaceX IPO | `SPACEX_IPO_THESIS/` | Feb 8, 2026 | `spacex-thumb.jpg` |
| Bubble & Logic — AI vs Dot-Com | `bubble-research/` | Feb 6, 2026 | `bubble-thumb.jpg` |
