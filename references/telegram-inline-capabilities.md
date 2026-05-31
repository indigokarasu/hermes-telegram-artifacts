# Telegram Inline Capabilities for Artifacts

Research from Telegram Bot API + Mini Apps docs, confirmed via testing (May 2026).

## Confirmed Working

### web_app InlineKeyboardButton — PRIMARY DELIVERY
- Message with button → user taps → Mini App panel slides up from bottom
- The `ARTIFACT:<id> <title>` prefix in `send_message` handles this automatically
- Artifact server injects `exitFullscreen()` → opens at half-screen (compact mode)
- **User preference: "the big nice button was actually nicer"** — confirmed preferred over all alternatives

### Bot Menu Button
- Configured via `setChatMenuButton` API → "Open Dashboard" on bot profile
- Opens the dashboard as a Mini App from the chat menu

### Inline mode (@hermes)
- Bot has `supports_inline_queries: True`
- User types `@hermes` → dropdown shows `InlineQueryResultArticle` cards
- Each card: title + description + thumbnail + optional web_app button
- Requires user to type `@hermes` first — not automatic

## Confirmed NOT Working

### answerWebAppQuery — BROKEN for web_app buttons
- `query_id` is NOT in `initDataUnsafe` when Mini App opens via `web_app` button
- Docs claim it should be available, but Telegram doesn't provide it in practice
- `WebAppInitData` docs say "is empty if launched from a keyboard button or from inline mode"
- Telegram apparently treats `web_app` buttons the same as keyboard buttons for this purpose
- The artifact server silently ignores it — no errors, no debug overlay

### URL link previews — OPENS BROWSER
- Sending artifact URL as a message → Telegram shows link preview card
- Tapping the preview opens the URL in an external browser, NOT inline
- Not useful for artifacts — user wants the Mini App experience

### InlineQueryResultWebApp — DOES NOT EXIST
- There is no `InlineQueryResultWebApp` type in the Bot API
- `web_app` only exists on `InlineKeyboardButton`, `KeyboardButton`, and `InlineQueryResultsButton`

## Not Yet Tested

### savePreparedInlineMessage
- Bot pre-stages an `InlineQueryResult` for the user to send via Mini App
- Returns `PreparedInlineMessage` with `id` and `expiration_date`
- Mini App calls `switchInlineQuery(preparedMessageId)` to present it
- Could work if the Mini App can coordinate with the bot server

### Direct Link with mode=compact
- `https://t.me/botusername/appname?startapp=command&mode=compact`
- Opens Mini App at half-screen height (Bot API 7.6+)
- Only works for direct links, not `web_app` buttons
- We achieve compact mode via `exitFullscreen()` injection instead

## Key Takeaway
Telegram does NOT render HTML content inline in chat messages. The `web_app` button is the closest to "inline interactive content" — it opens a Mini App panel from the bottom of the chat. This IS the right UX for artifacts.
