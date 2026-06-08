# Dynamic Artifact Patterns

Lessons learned from building the weather Mini App (2026-07).

## Loading States

Every artifact that fetches external data MUST show a loading state. The user sees a blank white screen otherwise, and thinks it's broken.

```html
<!-- Show this while loading -->
<div id="loading" class="loading">
  <div class="spinner"></div>
  <div>LOCATING…</div>
</div>

<!-- Hidden until data arrives -->
<div id="weather" style="display:none">
  <!-- actual content -->
</div>

<!-- Hidden unless error -->
<div id="error" class="error" style="display:none"></div>
```

CSS for the spinner (no external deps):
```css
.loading { text-align: center; padding: 40px 0; color: var(--muted); font-size: 12px; }
.loading .spinner {
  display: inline-block; width: 20px; height: 20px;
  border: 2px solid var(--border); border-top-color: var(--accent);
  border-radius: 50%; animation: spin 0.8s linear infinite; margin-bottom: 8px;
}
@keyframes spin { to { transform: rotate(360deg) } }
```

JS pattern:
```js
function showError(msg) {
  document.getElementById('loading').style.display = 'none';
  const el = document.getElementById('error');
  el.style.display = 'block';
  el.textContent = msg;
}

async function main() {
  try {
    const data = await fetchData();
    document.getElementById('loading').style.display = 'none';
    document.getElementById('weather').style.display = 'block';
    // populate DOM...
  } catch(e) {
    showError('ERROR: ' + e.message);
    console.error(e);
  }
}

main();
```

**Key:** Never leave the user staring at a blank screen. Always: loading → data OR error.

## IP Geolocation

For artifacts that need the user's location, ipapi.co is free, no auth, works from the browser:

```js
async function getLocation() {
  try {
    const d = await fetchJSON('https://ipapi.co/json/');
    if (d.latitude && d.longitude) {
      return { lat: d.latitude, lon: d.longitude, city: d.city || '', region: d.region || '' };
    }
  } catch(e) {}

  // Fallback: wttr.in IP-based location
  try {
    const d = await fetchJSON('https://wttr.in/?format=j1');
    const c = d.nearest_area[0];
    return {
      lat: parseFloat(c.latitude), lon: parseFloat(c.longitude),
      city: c.areaName[0].value,
      region: c.region ? c.region[0].value : ''
    };
  } catch(e) {}

  throw new Error('Could not determine location');
}
```

**Note:** IP geolocation from a server-side browser (like the Pi) will report the server's IP, NOT the user's. This pattern only works when the artifact runs in the user's Telegram WebView.

## Weather Data (open-meteo.com)

Free, no API key, generous rate limits. Returns JSON:

```js
async function getWeather(lat, lon) {
  return fetchJSON(
    `https://api.open-meteo.com/v1/forecast?` +
    `latitude=${lat}&longitude=${lon}` +
    `&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m,surface_pressure,uv_index,dew_point_2m,visibility` +
    `&hourly=temperature_2m,weather_code` +
    `&daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset` +
    `&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch` +
    `&timezone=auto&forecast_days=4`
  );
}
```

**Unit params:** `temperature_unit=fahrenheit`, `wind_speed_unit=mph`, `visibility` is in meters (convert: `/ 1609` for miles).

**WMO weather codes:** 0=Clear, 1=Mostly Clear, 2=Partly Cloudy, 3=Overcast, 45/48=Fog, 51-55=Drizzle, 61-65=Rain, 71-75=Snow, 80-82=Showers, 95-96=Thunderstorm.

## Fetch Helper

```js
async function fetchJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error('HTTP ' + r.status);
  return r.json();
}
```

## Wind Direction

```js
function windDir(deg) {
  const dirs = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW'];
  return dirs[Math.round(deg / 22.5) % 16];
}
```

## Time Formatting

```js
function formatHour(iso) {
  const d = new Date(iso);
  const h = d.getHours();
  if (h === 0) return '12AM';
  if (h === 12) return '12PM';
  return h > 12 ? (h - 12) + 'PM' : h + 'AM';
}

function dayName(iso) {
  return new Date(iso).toLocaleDateString('en-US', { weekday: 'short' });
}
```

## DOM Population Pattern

For dynamic content, use `textContent` for individual values and `createElement` for lists/grids. If you must use `innerHTML` for complex structures, ensure ALL interpolated values are from trusted sources (API data, not user input).

```js
// Single value: textContent via helper
function set(id, val) { document.getElementById(id).textContent = val; }
set('w-temp', Math.round(cur.temperature_2m));

// List: createElement in a loop
const hourlyEl = document.getElementById('w-hourly');
for (let i = 0; i < 8; i++) {
  const cell = document.createElement('div');
  cell.className = 'hour-cell';
  cell.innerHTML = `<div class="hour-time">${formatHour(w.hourly.time[i])}</div>`
    + `<div class="hour-temp">${Math.round(w.hourly.temperature_2m[i])}°</div>`
    + `<div class="hour-desc">${WMO_CODES[w.hourly.weather_code[i]] || ''}</div>`;
  hourlyEl.appendChild(cell);
}
```

## TG Lifecycle for Dynamic Artifacts

Same as static artifacts — wrap the init block and call it before your data fetch:

```js
const tg = (window.Telegram && window.Telegram.WebApp) ? window.Telegram.WebApp : null;
if (tg) {
  try {
    tg.ready();
    tg.expand();
    tg.setHeaderColor(tg.themeParams?.bg_color || '#0a0a0f');
    tg.setBackgroundColor(tg.themeParams?.bg_color || '#0a0a0f');
    tg.onEvent('themeChanged', function() {
      var p = tg.themeParams;
      if (p) { tg.setHeaderColor(p.bg_color); tg.setBackgroundColor(p.bg_color); }
    });
  } catch(e) {}
}

// Then fetch and render
main();
```

**Note:** `tg.expand()` is especially important for dynamic artifacts — the content needs the full viewport height.
