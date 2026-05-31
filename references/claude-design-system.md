# Claude visualizer — design system reference

A complete reference for building inline HTML/SVG widgets in Claude's visualizer. Written for agent handoff.

---

## How the visualizer works

The visualizer renders **raw HTML fragments or SVG** directly inline in the chat. No `<html>`, `<head>`, or `<body>` tags — just content. Output is streamed token-by-token; JS executes after the full fragment has landed.

**Two rendering modes:**
- SVG mode — output starts with `<svg`. Rendered as a static/animated vector graphic.
- HTML mode — everything else. Treated as a fragment, injected into a sandboxed context.

**Container:** `display: block; width: 100%` — 680px wide. No outer wrapper needed.

---

## Core philosophy

- **Seamless** — widgets should feel like a native extension of the chat UI.
- **Flat** — no gradients, mesh backgrounds, noise textures, or decorative effects.
- **Compact** — show the essential inline. Prose goes in the response, not inside the widget.
- **Text goes in the response, visuals go in the widget** — never put paragraphs of explanation inside HTML/SVG.

---

## Hard rules

- No `<!-- comments -->` or `/* comments */` — waste tokens, can break streaming.
- No `<html>`, `<head>`, `<body>`, or DOCTYPE.
- No `position: fixed` — collapses the iframe to 100px. Use faux-viewport divs for overlays.
- No gradients, drop shadows, blur, glow, or neon effects.
- No dark/colored backgrounds on outer containers — host provides the background.
- No emoji. Icons via Tabler outline webfont only (see Icons section).
- No `localStorage` or `sessionStorage` — blocked. Use JS variables or React state.
- No font-size below 11px.
- No tabs, carousels, or `display: none` during streaming — hidden content streams invisibly. Post-streaming JS-driven steppers are fine.
- No nested scrolling — auto-fit height.
- Sentence case always. Never Title Case or ALL CAPS.
- No mid-sentence bolding. Entity/class/function names go in `code` style.
- Round every displayed number — float math leaks artifacts (`0.1 + 0.2 = 0.30000000000000004`). Use `Math.round()`, `.toFixed(n)`, or `Intl.NumberFormat`.

---

## Streaming code order

```
<style>   ← short, keep under ~15 lines
HTML content
<script>  ← always last; executes after full stream
```

Prefer inline `style=""` over `<style>` blocks — controls must look correct mid-stream. Gradients, shadows, and blur flash during streaming DOM diffs; use solid flat fills instead.

---

## CSS variables

All auto-adapt to light/dark mode. **Never hardcode hex values for text or backgrounds** — invisible in dark mode.

### Backgrounds
| Variable | Description |
|---|---|
| `--color-background-primary` | White surface |
| `--color-background-secondary` | Subtle surface, metric cards |
| `--color-background-tertiary` | Page background |
| `--color-background-info` | Info tint |
| `--color-background-success` | Success tint |
| `--color-background-warning` | Warning tint |
| `--color-background-danger` | Danger tint |

### Text
| Variable | Description |
|---|---|
| `--color-text-primary` | Primary text (black in light mode) |
| `--color-text-secondary` | Muted text |
| `--color-text-tertiary` | Hint text |
| `--color-text-info` | Info text |
| `--color-text-success` | Success text |
| `--color-text-warning` | Warning text |
| `--color-text-danger` | Danger text |

### Borders
| Variable | Opacity | Use |
|---|---|---|
| `--color-border-tertiary` | 0.15α | Default borders |
| `--color-border-secondary` | 0.30α | Hover/emphasis |
| `--color-border-primary` | 0.40α | Strong borders |
| `--color-border-info/success/warning/danger` | — | Semantic borders |

### Typography
| Variable | Description |
|---|---|
| `--font-sans` | Anthropic Sans (default) |
| `--font-serif` | Editorial/blockquote only |
| `--font-mono` | Code snippets |

### Layout tokens
| Variable | Value | Use |
|---|---|---|
| `--border-radius-md` | 8px | Buttons, inputs, chips |
| `--border-radius-lg` | 12px | Cards (preferred) |
| `--border-radius-xl` | 16px | Large panels |

---

## Typography rules

| Element | Size | Weight |
|---|---|---|
| h1 | 22px | 500 |
| h2 | 18px | 500 |
| h3 | 16px | 500 |
| Body | 16px | 400, line-height 1.7 |
| Small/labels | 13px | 400 |
| Micro | 11px min | 400 |

**Two weights only: 400 and 500.** Never 600 or 700 — too heavy against the host UI.

---

## Color palette

9 ramps × 7 stops. 50 = lightest fill, 800/900 = text on light fills.

| Class | Ramp | 50 | 100 | 200 | 400 | 600 | 800 | 900 |
|---|---|---|---|---|---|---|---|---|
| `c-purple` | Purple | #EEEDFE | #CECBF6 | #AFA9EC | #7F77DD | #534AB7 | #3C3489 | #26215C |
| `c-teal` | Teal | #E1F5EE | #9FE1CB | #5DCAA5 | #1D9E75 | #0F6E56 | #085041 | #04342C |
| `c-coral` | Coral | #FAECE7 | #F5C4B3 | #F0997B | #D85A30 | #993C1D | #712B13 | #4A1B0C |
| `c-pink` | Pink | #FBEAF0 | #F4C0D1 | #ED93B1 | #D4537E | #993556 | #72243E | #4B1528 |
| `c-gray` | Gray | #F1EFE8 | #D3D1C7 | #B4B2A9 | #888780 | #5F5E5A | #444441 | #2C2C2A |
| `c-blue` | Blue | #E6F1FB | #B5D4F4 | #85B7EB | #378ADD | #185FA5 | #0C447C | #042C53 |
| `c-green` | Green | #EAF3DE | #C0DD97 | #97C459 | #639922 | #3B6D11 | #27500A | #173404 |
| `c-amber` | Amber | #FAEEDA | #FAC775 | #EF9F27 | #BA7517 | #854F0B | #633806 | #412402 |
| `c-red` | Red | #FCEBEB | #F7C1C1 | #F09595 | #E24B4A | #A32D2D | #791F1F | #501313 |

### Light/dark mode quick pick

- **Light mode:** 50 fill + 600 stroke + **800 title / 600 subtitle**
- **Dark mode:** 800 fill + 200 stroke + **100 title / 200 subtitle**

### Color assignment rules

- Color encodes **meaning**, not sequence. Don't rainbow-cycle.
- Group nodes by **category** — all nodes of the same type share one ramp.
- Use **gray** for neutral/structural nodes (start, end, generic steps).
- Use **2–3 ramps per diagram**, not 6+.
- **Prefer purple, teal, coral, pink** for general categories.
- Reserve blue/green/amber/red for semantic meaning (info/success/warning/danger).
- Text on colored bg: always use 800 or 900 from the **same ramp** — never `--color-text-primary`.
- When a box has title + subtitle, use two different stops — 800 title / 600 subtitle in light mode.

---

## Spacing tokens

| Use | Value |
|---|---|
| Vertical rhythm | rem — 1rem, 1.5rem, 2rem |
| Component gaps | px — 8px, 12px, 16px |
| Card padding | 1rem 1.25rem |
| Border width | 0.5px always. 2px only for featured card accent (one exception). |
| Box shadow | None, except `box-shadow: 0 0 0 Npx` focus rings |

---

## Component patterns

### Cards

**Raised card** (bounded objects, records):
```html
<div style="background: var(--color-background-primary); border-radius: var(--border-radius-lg); border: 0.5px solid var(--color-border-tertiary); padding: 1rem 1.25rem;">
  ...
</div>
```

**Metric card** (summary numbers):
```html
<div style="background: var(--color-background-secondary); border-radius: var(--border-radius-md); padding: 1rem;">
  <p style="font-size: 13px; color: var(--color-text-secondary); margin: 0 0 4px;">Label</p>
  <p style="font-size: 24px; font-weight: 500; margin: 0;">42</p>
</div>
```

Use metric cards in grids of 2–4 with `gap: 12px`.

### Responsive grid

```css
display: grid;
grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
gap: 12px;
```

Use `minmax(0, 1fr)` (not `1fr`) to prevent grid children from overflowing the container.

### Form elements

Form elements are pre-styled — write bare tags:
- `<input type="text">` — 36px height, hover/focus built in
- `<input type="range">` — 4px track, 18px thumb
- `<button>` — transparent bg, 0.5px border, hover/active built in
- `<select>`, `<textarea>` — also pre-styled

Add `↗` to button labels that trigger `sendPrompt()`.

### No rounded corners on single-sided borders

If using `border-left` or `border-top` accents, set `border-radius: 0`. Rounded corners only work with full borders.

### Modal/overlay pattern

Never use `position: fixed`. Instead:
```html
<div style="min-height: 400px; background: rgba(0,0,0,0.45); display: flex; align-items: center; justify-content: center;">
  <!-- modal content here -->
</div>
```

---

## Icons

Tabler outline webfont is pre-loaded. Use `<i class="ti ti-name">` — inherits color and font-size from parent.

- **Outline only** — never `-filled` suffixes (`ti-heart-filled` etc. are not loaded).
- Decorative icons: `aria-hidden="true"`
- Icon-only buttons: `aria-label="..."`
- Sizing: 16–20px inline, 24px max decorative

Common icons: `ti-home` `ti-settings` `ti-user` `ti-search` `ti-x` `ti-check` `ti-plus` `ti-trash` `ti-edit` `ti-download` `ti-upload` `ti-file` `ti-folder` `ti-chart-bar` `ti-calendar` `ti-clock` `ti-arrow-right` `ti-arrow-left` `ti-chevron-down` `ti-external-link` `ti-copy` `ti-refresh` `ti-player-play` `ti-player-pause` `ti-heart` `ti-star` `ti-bell` `ti-mail` `ti-lock` `ti-eye` `ti-menu-2`

Do not hand-draw icon SVG paths.

---

## CDN allowlist (CSP-enforced)

Only these origins are permitted. All others silently fail:

- `cdnjs.cloudflare.com`
- `cdn.jsdelivr.net`
- `esm.sh`
- `unpkg.com`
- `fonts.googleapis.com`
- `fonts.gstatic.com`

### Available libraries (HTML/React)

Load UMD builds via `<script src="...">` — sets a global. Follow with a plain `<script>` (no `type="module"`).

| Library | CDN path |
|---|---|
| Chart.js 4.4.1 | `cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js` |
| D3 7.8.5 | `cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js` |
| TopoJSON 3.0.2 | `cdnjs.cloudflare.com/ajax/libs/topojson/3.0.2/topojson.min.js` |
| Mermaid 11 | `esm.sh/mermaid@11/dist/mermaid.esm.min.mjs` (ESM only) |

In React artifacts: recharts, mathjs, lodash, d3, plotly, three (r128), papaparse, SheetJS, shadcn/ui, chart.js, tone, mammoth, tensorflow are pre-bundled.

---

## `sendPrompt(text)`

A global function injected into every widget. Sends a message to the chat as if the user typed it.

```javascript
sendPrompt('Analyze this data for me');
```

Use for actions that benefit from Claude thinking. Handle filtering, sorting, toggling, and calculations in JS instead.

Append `↗` to button labels that call `sendPrompt`.

---

## Storage

`localStorage` and `sessionStorage` are blocked.

For cross-session persistence, use the `window.storage` API:

```javascript
// Store
await window.storage.set('key', JSON.stringify(data));
await window.storage.set('key', JSON.stringify(data), true); // shared=true: visible to all users

// Retrieve
const result = await window.storage.get('key');
const data = result ? JSON.parse(result.value) : null;

// List
const { keys } = await window.storage.list('prefix:');

// Delete
await window.storage.delete('key');
```

Key rules:
- Under 200 chars, no whitespace, no `/`, `\`, or quotes
- Values under 5MB per key
- Last-write-wins for concurrent updates
- Always wrap in try/catch — accessing a missing key throws

---

## Accessibility

**HTML widgets:** Begin with a visually-hidden heading:
```html
<h2 class="sr-only">One-sentence summary for screen readers</h2>
```

**SVG widgets:** Use `role="img"` with `<title>` and `<desc>` as first children:
```svg
<svg width="100%" viewBox="0 0 680 400" role="img">
  <title>Short title</title>
  <desc>Longer description of what the diagram shows.</desc>
  ...
</svg>
```

---

## SVG setup

### ViewBox

**Always `viewBox="0 0 680 H"`** — 680 is load-bearing. With `width="100%"`, the browser scales the coordinate space 1:1 to the 680px container. Changing the viewBox width scales all text and shapes unexpectedly.

Set H = bottom-most element's y + height + 40px buffer. Don't guess; measure.

Safe area: x=40 to x=640, y=40 to y=(H-40).

### Arrow marker (include in every SVG defs)

```svg
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
  </marker>
</defs>
```

Use `marker-end="url(#arrow)"` on lines. The head inherits `context-stroke` — color always matches the line.

### Pre-built SVG classes

| Class | Description |
|---|---|
| `class="t"` | Sans 14px primary text |
| `class="ts"` | Sans 12px secondary text |
| `class="th"` | Sans 14px medium (500) text |
| `class="box"` | Neutral rect (bg-secondary fill, border stroke) |
| `class="node"` | Clickable group — cursor pointer, hover dim |
| `class="arr"` | Arrow line — 1.5px, open chevron head |
| `class="leader"` | Dashed leader line — 0.5px, tertiary stroke |
| `class="c-{ramp}"` | Colored node — apply to `<g>`, `<rect>`, `<circle>`, `<ellipse>`. NOT `<path>`. Dark mode automatic. |

Every `<text>` must carry one of `t`, `ts`, `th`. Unclassed text inherits default sans — the tell you forgot the class.

### c-{ramp} nesting

These classes use direct-child selectors. Nesting a `<g>` inside a `<g class="c-blue">` makes shapes grandchildren — they lose the fill and render black. Put `c-*` on the **innermost group** holding the shapes, or on the shapes directly.

### Text rules

- **Two font sizes only:** 14px for node/region labels, 12px for subtitles/descriptions/arrow labels.
- `dominant-baseline="central"` on every `<text>` inside a box (centers vertically).
- `<text>` never auto-wraps. Every line break needs an explicit `<tspan x="..." dy="1.2em">`.
- `text-anchor="end"` at x<60 is risky — long labels extend past x=0.

### Font width calibration (Anthropic Sans, for box sizing)

| Text | Chars | Weight | Size | Rendered width |
|---|---|---|---|---|
| Authentication Service | 22 | 500 | 14px | ~167px |
| Background Job Processor | 24 | 500 | 14px | ~201px |
| Detects and validates incoming tokens | 37 | 400 | 14px | ~279px |
| forwards request to | 19 | 400 | 12px | ~123px |

Rule: box width = max(title_chars × 8, subtitle_chars × 7) + 24px padding.

### Connector paths

Every `<path>` used as a connector must have `fill="none"` — SVG defaults to `fill: black`.

If a direct arrow path would cross another box, route around with an L-bend:
```svg
<path d="M x1 y1 L x1 ymid L x2 ymid L x2 y2" fill="none" class="arr" marker-end="url(#arrow)"/>
```

### Stroke widths

- Diagram borders and edges: 0.5px
- Tank shells, structural outlines: 1–2.5px
- Never 2px except for featured card accents in HTML

### What goes in `<defs>`

Only: arrow marker, one `<clipPath>`, subtle `<pattern>` fills (secondary visual cue for categorical data), one `<linearGradient>` in illustrative diagrams only. No filters, no extra markers.

---

## Diagram types

### Flowchart

Sequential processes, cause-and-effect, decision trees.

- Prefer single-direction flows (all top-down or all left-right).
- Max 4–5 nodes per diagram. Complex diagrams → split into multiple calls.
- 60px minimum between boxes, 24px padding inside boxes.
- Two-line boxes need at least 56px height, 22px between lines.
- Cycles don't get drawn as rings — use HTML steppers or a linear layout with a return arrow.

**Single-line node (44px):**
```svg
<g class="node c-blue" onclick="sendPrompt('...')">
  <rect x="100" y="20" width="180" height="44" rx="8" stroke-width="0.5"/>
  <text class="th" x="190" y="42" text-anchor="middle" dominant-baseline="central">Label</text>
</g>
```

**Two-line node (56px):**
```svg
<g class="node c-blue" onclick="sendPrompt('...')">
  <rect x="100" y="20" width="200" height="56" rx="8" stroke-width="0.5"/>
  <text class="th" x="200" y="38" text-anchor="middle" dominant-baseline="central">Title</text>
  <text class="ts" x="200" y="56" text-anchor="middle" dominant-baseline="central">Subtitle text</text>
</g>
```

**Connector:**
```svg
<line x1="200" y1="76" x2="200" y2="120" class="arr" marker-end="url(#arrow)"/>
```

### Structural diagram

Things inside other things. Containment as the primary concept.

- Outermost container: large rounded rect, rx=20–24, 50-stop fill, 0.5px stroke (600 stop).
- Inner regions: rx=8–12, 100–200 stop fill. Different ramp from parent if semantically distinct.
- 20px minimum padding inside every container.
- Max 2–3 nesting levels.

### Database schemas / ERDs

Use mermaid.js `erDiagram`, not SVG. Import via `esm.sh`:

```html
<div id="erd"></div>
<script type="module">
import mermaid from 'https://esm.sh/mermaid@11/dist/mermaid.esm.min.mjs';
const dark = matchMedia('(prefers-color-scheme: dark)').matches;
await document.fonts.ready;
mermaid.initialize({
  startOnLoad: false, theme: 'base',
  fontFamily: '"Anthropic Sans", sans-serif',
  themeVariables: {
    darkMode: dark, fontSize: '13px',
    fontFamily: '"Anthropic Sans", sans-serif',
    lineColor: dark ? '#9c9a92' : '#73726c',
    textColor: dark ? '#c2c0b6' : '#3d3d3a',
  },
});
const { svg } = await mermaid.render('erd-svg', `erDiagram
  USERS ||--o{ POSTS : writes
  POSTS ||--o{ COMMENTS : has`);
document.getElementById('erd').innerHTML = svg;
</script>
```

### Illustrative diagram

For building intuition. Physical subjects get cross-sections; abstract subjects get spatial metaphors.

**What changes from flowchart rules:**
- Shapes are freeform — `<path>`, `<ellipse>`, `<circle>`, `<polygon>`, curves.
- Layout follows the subject's geometry, not a grid.
- Color encodes intensity (warm = hot/active, cool = cold/dormant), not category.
- Layering and overlap are allowed — for shapes only. **Text never gets crossed by strokes.**
- One `<linearGradient>` per diagram is permitted — only to show a continuous physical property.
- Animation allowed: CSS `@keyframes` on `transform` and `opacity` only. Wrap in `@media (prefers-reduced-motion: no-preference)`.
- Labels go in the margins with leader lines (0.5px dashed), not inside the drawing.

**Interactive preference:** If the real system has a control, give the diagram that control — slider, toggle, clickable element. Reach for HTML with inline SVG first; only fall back to static SVG when there's nothing to interact with.

---

## Chart.js rules

```html
<div style="position: relative; width: 100%; height: 300px;">
  <canvas id="myChart" role="img" aria-label="Description of chart">Fallback text.</canvas>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<script>
  new Chart(document.getElementById('myChart'), {
    type: 'bar',
    data: { labels: ['Q1','Q2','Q3','Q4'], datasets: [{ label: 'Revenue', data: [12,19,8,15] }] },
    options: { responsive: true, maintainAspectRatio: false }
  });
</script>
```

- Every `<canvas>` must have `role="img"`, `aria-label`, and fallback text inside the tags.
- Never rely on color alone — pair with dash pattern, marker shape, or fill pattern.
- Canvas cannot resolve CSS variables. Use hardcoded hex.
- Set height only on the wrapper div, never on the canvas element.
- For horizontal bar charts: wrapper height ≥ (num_bars × 40) + 80px.
- Disable Chart.js default legend and build custom HTML legend.
- `autoSkip: false, maxRotation: 45` if you need all x-axis labels visible.
- Negative values: `-$5M` not `$-5M` — sign before currency symbol.

---

## Geographic maps (D3 choropleth)

Never invent coordinates. Fetch real topology from allowed CDNs only.

| Coverage | URL | Projection | Object key |
|---|---|---|---|
| US states | `cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json` | `d3.geoAlbersUsa()` | `.states` |
| World countries | `cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json` | `d3.geoNaturalEarth1()` | `.countries` |
| Country subdivisions | `cdn.jsdelivr.net/npm/datamaps@0.5.10/src/js/data/{iso3}.topo.json` | varies | `.{iso3}` |

Always `web_fetch` the topology URL first to confirm the real feature `id` and `properties.name` values before writing the widget.

---

## Layout patterns

### Editorial (explanatory content)
No card wrapper. Prose flows naturally. Whitespace is the container.

### Card (bounded objects)
Single raised card wraps everything. Use for contact records, receipts, data records.

### Dashboard
Metric cards in a grid above the chart canvas. Chart has no card wrapper.

### Mockup presentation
Contained mockups (mobile screens, modals, small components) sit on a `--color-background-secondary` surface with `border-radius: var(--border-radius-lg)` and padding. Full-width mockups (dashboards, settings pages) do not need an outer wrapper.

---

## Diagram routing quick reference

| User says | Diagram type | What to draw |
|---|---|---|
| "how does X work" | Illustrative | Spatial metaphor or cross-section of the mechanism |
| "explain X" / "I don't get X" | Illustrative | Abstract spatial metaphor |
| "X architecture" / "show the structure of X" | Structural | Labelled containment boxes |
| "what are the steps" / "walk me through the process" | Flowchart | Sequential boxes and arrows |
| "draw the schema" / "show the ERD" | mermaid.js erDiagram | Entity-relationship diagram |
| "how does the X handshake/sequence work" | Flowchart | Steps with arrows |
| "explain the Krebs cycle" / "how does the event loop work" | HTML stepper | Click-through stages |

---

## ViewBox safety checklist

Before finalizing any SVG:

1. Find bottom-most element: `max(y + height)` across all rects. Set viewBox height = that value + 40.
2. Find rightmost element: `max(x + width)`. Must be ≤ 640.
3. For `text-anchor="end"`, text extends left from x. Verify it doesn't go past x=0.
4. Check all unrelated element pairs for unintentional overlap.
5. For same-row boxes: verify `left_box.x + left_box.width + 20 ≤ right_box.x`.
6. Never use negative x or y coordinates.

---

## Complexity budget

- Box subtitles: ≤5 words
- Colors: ≤2 ramps per diagram (3 max)
- Horizontal tier: ≤4 boxes at full width (~140px each); 5+ → shrink or split
- Nodes per diagram: ≤4–5 for flowcharts; split complex topics across multiple diagrams

---

## Multiple diagrams

- **Never stack diagram tool calls back-to-back.** Always write prose between them.
- Only use `sendPrompt()` for actions that need Claude to think. JS handles filtering, sorting, toggling.
- For complex topics, prefer a series of smaller diagrams over one dense diagram.
