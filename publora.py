"""Publora for Sublime Text.

Sends the selected text, or the whole file, to Publora as a scheduled post
or a draft. Talks to one host only: https://api.publora.com
"""

import json
import threading
import urllib.error
import urllib.request

import sublime
import sublime_plugin

BASE_URL = "https://api.publora.com/api/v1"
KEYS_URL = "https://app.publora.com/dashboard/api"
SETTINGS_FILE = "Publora.sublime-settings"

# Networks that reject a post without an image or video.
MEDIA_REQUIRED = ("instagram", "tiktok", "youtube")


def api_key():
    return sublime.load_settings(SETTINGS_FILE).get("api_key", "").strip()


def call_api(method, path, body=None):
    """One request to Publora. Raises RuntimeError with a readable message."""
    request = urllib.request.Request(
        BASE_URL + path,
        method=method,
        data=json.dumps(body).encode() if body else None,
        headers={
            "x-publora-key": api_key(),
            "Content-Type": "application/json",
            "User-Agent": "sublime-publora/1.0.0",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raise RuntimeError(describe(error))
    except urllib.error.URLError as error:
        raise RuntimeError("Could not reach Publora: %s" % error.reason)


def describe(error):
    """Show the API's own message rather than a bare status code."""
    if error.code == 401:
        return "Publora rejected the API key. Set it in Preferences, Package Settings, Publora."
    if error.code == 429:
        return "Publora rate limit reached. Try again in a moment."

    detail = ""
    try:
        body = json.loads(error.read().decode())
        detail = body.get("error") or body.get("message") or ""
    except Exception:
        pass
    return "Publora error %s%s" % (error.code, ": " + detail if detail else "")


def in_background(work, done):
    """Keep the editor responsive: network off the UI thread, result back on it."""
    def run():
        try:
            result = work()
            sublime.set_timeout(lambda: done(result, None), 0)
        except Exception as error:
            sublime.set_timeout(lambda: done(None, error), 0)

    threading.Thread(target=run, daemon=True).start()


class PubloraSendCommand(sublime_plugin.TextCommand):
    """Publora: Send selection (falls back to the whole file)."""

    def run(self, edit, whole_file=False):
        if not api_key():
            self.offer_setup()
            return

        text = self.gather(whole_file)
        if not text.strip():
            sublime.status_message("Publora: nothing to send")
            return

        self.text = text.strip()
        sublime.status_message("Publora: loading your accounts…")
        in_background(lambda: call_api("GET", "/platform-connections"), self.on_connections)

    def gather(self, whole_file):
        view = self.view
        if whole_file:
            return view.substr(sublime.Region(0, view.size()))

        parts = [view.substr(region) for region in view.sel() if not region.empty()]
        return "\n\n".join(parts) if parts else view.substr(sublime.Region(0, view.size()))

    def offer_setup(self):
        message = "Publora needs an API key. Open the settings now?"
        if sublime.ok_cancel_dialog(message, "Open settings"):
            self.view.window().run_command(
                "edit_settings",
                {
                    "base_file": "${packages}/Publora/Publora.sublime-settings",
                    "default": '{\n\t"api_key": "sk_…"  // from %s\n}\n' % KEYS_URL,
                },
            )

    def on_connections(self, data, error):
        if error:
            sublime.error_message(str(error))
            return

        connections = data if isinstance(data, list) else data.get("connections", [])
        self.connections = [c for c in connections if c.get("platformId")]

        if not self.connections:
            sublime.error_message("No connected accounts yet. Connect one in the Publora dashboard first.")
            return

        items = [
            [c.get("username") or c.get("displayName") or c["platformId"], c["platformId"]]
            for c in self.connections
        ]
        self.view.window().show_quick_panel(items, self.on_channel, placeholder="Publora: where should this go?")

    def on_channel(self, index):
        if index < 0:
            return

        self.platform = self.connections[index]["platformId"]

        if self.platform.startswith(MEDIA_REQUIRED):
            sublime.error_message(
                "%s needs an image or video, which this version does not send. "
                "Attach it in the Publora dashboard." % self.platform.split("-")[0]
            )
            return

        self.view.window().show_quick_panel(
            [
                ["Save as draft", "Nothing is published. Review it in the Publora dashboard."],
                ["Schedule for a time", "Enter a date and time in UTC."],
            ],
            self.on_mode,
            placeholder="Publora: draft or scheduled?",
        )

    def on_mode(self, index):
        if index < 0:
            return
        if index == 0:
            self.send(None)
            return

        self.view.window().show_input_panel(
            "Publora: when? (UTC, e.g. 2026-09-01T12:00:00Z)",
            "",
            self.send,
            None,
            None,
        )

    def send(self, when):
        payload = {"content": self.text, "platforms": [self.platform]}
        if when:
            payload["scheduledTime"] = when.strip()

        sublime.status_message("Publora: sending…")
        in_background(lambda: call_api("POST", "/create-post", payload), self.on_sent)

    def on_sent(self, result, error):
        if error:
            sublime.error_message(str(error))
            return

        post_id = (result or {}).get("postGroupId") or (result or {}).get("id") or ""
        sublime.status_message("Publora: done. %s" % post_id)
        sublime.message_dialog("Publora: the post was created.\n\nPost group ID: %s" % (post_id or "unknown"))
