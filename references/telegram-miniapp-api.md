# Telegram Mini Apps API — Capabilities Reference

Condensed from https://core.telegram.org/bots/webapps (Bot API 9.5+, as of May 2026).
Focus: features relevant to dashboard/artifact content inside Telegram's WebView.

## Initialization

```html
<script src="https://telegram.org/js/telegram-web-app.js?62"></script>
<script>
const tg = window.Telegram.WebApp;
tg.ready();    // signals loading complete, hides placeholder
tg.expand();   // expand to full available height
</script>
```

**`window.Telegram.WebApp` key fields:**

| Field | What it tells you |
|-------|-------------------|
| `initData` | Raw auth string (validate server-side with HMAC-SHA256) |
| `initDataUnsafe` | Parsed object (client display only, NEVER trust for auth) |
| `version` | Bot API version on user's client |
| `platform` | `"android"`, `"ios"`, `"web"`, `"macos"`, `"tdesktop"` |
| `colorScheme` | `"light"` or `"dark"` |
| `themeParams` | Theme color object (see below) |
| `isActive` | 8.0+ — true when Mini App is active (not minimized) |
| `isExpanded` | true when expanded to max height |
| `viewportHeight` / `viewportStableHeight` | Current / stable visible area height |
| `isFullscreen` | 8.0+ — true in fullscreen mode |
| `isClosingConfirmationEnabled` | Whether close confirmation is active |
| `safeAreaInset` | 8.0+ — device safe area (notch/Dynamic Island) |
| `contentSafeAreaInset` | 8.0+ — safe area excluding Telegram UI chrome |

## ThemeParams — 15 color fields (CSS variables available)

Every field is optional. Each also has a `var(--tg-theme-*)` CSS variable that updates in real time.

| Field | CSS Variable | Description |
|-------|-------------|-------------|
| `bg_color` | `--tg-theme-bg-color` | Main background |
| `text_color` | `--tg-theme-text-color` | Primary text |
| `hint_color` | `--tg-theme-hint-color` | Hint/muted text |
| `link_color` | `--tg-theme-link-color` | Link color |
| `button_color` | `--tg-theme-button-color` | Button fill |
| `button_text_color` | `--tg-theme-button-text-color` | Button text |
| `secondary_bg_color` | `--tg-theme-secondary-bg-color` | Secondary background (6.1+) |
| `header_bg_color` | `--tg-theme-header-bg-color` | Header background (7.0+) |
| `bottom_bar_bg_color` | `--tg-theme-bottom-bar-bg-color` | Bottom bar (7.10+) |
| `accent_text_color` | `--tg-theme-accent-text-color` | Accent text (7.0+) |
| `section_bg_color` | `--tg-theme-section-bg-color` | Section background (7.0+) |
| `section_header_text_color` | `--tg-theme-section-header-text-color` | Section header text (7.0+) |
| `section_separator_color` | `--tg-theme-section-separator-color` | Separator (7.6+) |
| `subtitle_text_color` | `--tg-theme-subtitle-text-color` | Subtitle text (7.0+) |
| `destructive_text_color` | `--tg-theme-destructive-text-color` | Destructive actions (7.0+) |

**Best practice:** Map your CSS vars to `var(--tg-theme-*)` as the primary source, with fallbacks. This gives automatic support for all Telegram themes including custom ones — not just light/dark binary.

```css
:root {
  --bg: var(--tg-theme-bg-color, #f5f5f5);
  --fg: var(--tg-theme-text-color, #1a1a1a);
  --muted: var(--tg-theme-hint-color, #666);
  --accent: var(--tg-theme-accent-text-color, #0ea5e9);
  --card: var(--tg-theme-section-bg-color, #ffffff);
  --border: var(--tg-theme-section-separator-color, #e0e0e0);
}
```

## Color control methods

```js
tg.setHeaderColor('#RRGGBB');     // or 'bg_color', 'secondary_bg_color'
tg.setBackgroundColor('#RRGGBB');
tg.setBottomBarColor('#RRGGBB');  // 7.10+
```

## BottomButton (formerly MainButton)

Sticky action button at the bottom of the Mini App. There are two: `MainButton` and `SecondaryButton`.

```js
tg.MainButton.setText('Refresh');
tg.MainButton.show();
tg.MainButton.onClick(() => { /* ... */ });
// Loading state:
tg.MainButton.showProgress();
tg.MainButton.hideProgress();
// Shine effect (7.10+):
tg.MainButton.setParams({ has_shine_effect: true });
// Custom emoji icon (9.5+):
tg.MainButton.setParams({ icon_custom_emoji_id: '...' });
// SecondaryButton position (left/right/top/bottom):
tg.SecondaryButton.setParams({ position: 'left' });
tg.SecondaryButton.show();
```

**SecondaryButton** (7.10+) — same API as MainButton. Default text "Cancel".

## BackButton

```js
tg.BackButton.show();
tg.onEvent('backButtonClicked', () => { /* navigate back */ });
```

Useful for in-app navigation stacks (file browser, modal drill-downs).

## SettingsButton

```js
tg.SettingsButton.show();
tg.onEvent('settingsButtonClicked', () => { /* open settings panel */ });
```

Adds "Settings" to the Mini App's three-dot context menu.

## CloudStorage

Per-user key-value storage synced across devices. Up to 1024 items, 4096 chars each.

```js
tg.CloudStorage.setItem('pref_tab', 'system', (err, ok) => {});
tg.CloudStorage.getItem('pref_tab', (err, val) => { /* val */ });
tg.CloudStorage.getItems(['pref_tab', 'pref_theme'], (err, vals) => { /* {key: val} */ });
tg.CloudStorage.removeItems(['pref_tab'], (err, ok) => {});
tg.CloudStorage.getKeys((err, keys) => { /* ['pref_tab', ...] */ });
```

**vs localStorage:** localStorage persists on the device only (no cross-device sync), may expire on iOS after ~7 days unused. CloudStorage persists indefinitely and syncs. Use CloudStorage for user preferences; localStorage for temporary UI state.

## DeviceStorage / SecureStorage (9.0+)

```js
// DeviceStorage — 5MB persistent local storage
tg.DeviceStorage.setItem('key', 'value', cb);
tg.DeviceStorage.getItem('key', cb);

// SecureStorage — 10 items, OS-level (Keychain/Keystore)
tg.SecureStorage.setItem('key', 'value', cb);
tg.SecureStorage.getItem('key', cb);
```

## Safe Area Insets (8.0+)

Apply padding for device notches / Dynamic Island / Telegram UI:

```css
body {
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
}
```

Or read programmatically:
```js
const safe = tg.safeAreaInset;          // {top, bottom, left, right}
const content = tg.contentSafeAreaInset; // content area excluding Telegram chrome
```

## Full-screen Mode (8.0+)

```js
tg.requestFullscreen();
tg.exitFullscreen();
tg.lockOrientation();   // lock to current orientation
tg.unlockOrientation();
```

## Home Screen Shortcuts (8.0+)

```js
tg.addToHomeScreen();   // prompt user to add shortcut
tg.checkHomeScreenStatus((status) => {
  // 'unsupported' | 'unknown' | 'added' | 'missed'
});
```

## Closing Confirmation (6.2+)

```js
tg.enableClosingConfirmation();   // prevent accidental close
tg.disableClosingConfirmation();
```

## Events

```js
tg.onEvent('themeChanged', () => { /* re-read themeParams/colorScheme */ });
tg.onEvent('viewportChanged', (e) => { /* e.isStateStable */ });
tg.onEvent('activated', () => { /* resumed from minimized */ });
tg.onEvent('deactivated', () => { /* minimized/backgrounded */ });
tg.onEvent('mainButtonClicked', () => { /* ... */ });
tg.onEvent('secondaryButtonClicked', () => { /* ... */ });
tg.onEvent('backButtonClicked', () => { /* ... */ });
tg.onEvent('settingsButtonClicked', () => { /* ... */ });
tg.onEvent('safeAreaChanged', () => { /* re-read safeAreaInset */ });
tg.onEvent('contentSafeAreaChanged', () => { /* re-read contentSafeAreaInset */ });
tg.onEvent('fullscreenChanged', () => { /* toggle UI */ });
```

**Key pattern — pause on deactivate:**
```js
let polling = setInterval(fetchData, 30000);
tg.onEvent('deactivated', () => { clearInterval(polling); polling = null; });
tg.onEvent('activated', () => { if (!polling) polling = setInterval(fetchData, 30000); });
```

## Other capabilities

- **HapticFeedback** — `impactOccurred('light'|'medium'|'heavy'|'rigid'|'soft')`, `notificationOccurred('success'|'warning'|'error')`, `selectionChanged()`
- **BiometricManager** (7.2+) — fingerprint/Face ID auth
- **Accelerometer / Gyroscope / DeviceOrientation** (8.0+) — sensor data
- **LocationManager** (8.0+) — GPS with permission
- **QR Scanner** — `showScanQrPopup()` / `closeScanQrPopup()`
- **Clipboard** — `readTextFromClipboard()`
- **Share** — `shareMessage()`, `shareToStory()` (7.8+)
- **Popups** — `showPopup()`, `showAlert()`, `showConfirm()`
- **Navigation** — `openLink()`, `openTelegramLink()`, `openInvoice()`

## Version detection

```js
if (tg.isVersionAtLeast('8.0')) {
  // safe to use requestFullscreen, safeAreaInset, addToHomeScreen, etc.
}
```

## Our current dashboard usage (homelab-widget.html)

**All major API features now used (as of 2026-05-29):**

- `ready`, `expand`, `colorScheme`, `themeParams`
- `setHeaderColor`, `setBackgroundColor`, `setBottomBarColor` — all synced to theme
- `HapticFeedback` — light/medium/heavy on interactions
- `enableVerticalSwipes` — pull-to-refresh gesture
- `enableClosingConfirmation` — prevent accidental close
- `BackButton` — auto-shows for modal navigation, pops modal on press
- `SecondaryButton` — refresh action (↻) with haptic feedback
- `SettingsButton` — opens Settings modal from three-dot menu
- `CloudStorage` — cross-device synced prefs (active tab, active view)
- `DeviceStorage`/`SecureStorage` — wrappers for iOS localStorage expiry protection
- `isActive`/`deactivated` events — pause 30s polling when backgrounded
- `themeChanged` event — live theme switching
- `addToHomeScreen` — available from Settings modal
- CSS variables mapped to `--tg-theme-*` via `@supports` progressive enhancement + `applyTelegramTheme()` JS

**Not yet used:** `requestFullscreen`, `BiometricManager`, sensors, QR scanner, `shareMessage`
