# Publora for Sublime Text

Select the text, run one command, and it goes out. This package sends the selection, or the whole file, to [Publora](https://publora.com?utm_source=sublime&utm_medium=package) as a scheduled post or a draft.

Ten networks: LinkedIn, X, Instagram, Threads, TikTok, YouTube, Facebook, Bluesky, Mastodon and Telegram.

## Commands

Open the command palette and type `Publora`:

- **Publora: Send selection** sends what you selected, or the whole file when nothing is selected.
- **Publora: Send this file** sends the whole file regardless.

You then pick the channel, and choose between a draft and a scheduled time.

## Setup

1. Create a Publora account at [publora.com](https://publora.com?utm_source=sublime&utm_medium=package). The free plan is 15 posts a month and three connected accounts, no card needed.
2. Connect at least one social account in the Publora dashboard. The package publishes to accounts connected there; it cannot connect them for you.
3. Open [Settings → API keys](https://app.publora.com/dashboard/api?utm_source=sublime&utm_medium=package) and press Generate API key.
4. In Sublime Text: **Preferences → Package Settings → Publora → Settings**, paste the key into `api_key`.

## Things worth knowing

**Drafts are offered first.** Choosing "Save as draft" publishes nothing: the post waits in Publora until you look at it.

**Instagram, TikTok and YouTube need media.** They reject text-only posts, and this version sends text only. The package says so instead of failing quietly.

**Nothing blocks the editor.** Network calls run on a background thread, so Sublime stays responsive while a post is sent.

**Your key stays in your settings.** It is sent only to `https://api.publora.com` in a request header. The package talks to no other host and stores nothing.

## Licence

MIT
