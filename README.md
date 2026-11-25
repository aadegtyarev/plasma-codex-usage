# plasma-codex-usage

A small KDE Plasma 5 panel widget that shows how much of your OpenAI Codex subscription limit is left: the OpenAI logo and a percentage.

- The tooltip says which limit it is (weekly or 5-hour), when it resets and how many free limit resets you have.
- The percentage turns orange at 20% and red at 10%.
- A click opens a menu: **Refresh** and **Open usage page** (chatgpt.com/settings/usage). The same items are in the right-click menu.
- If Codex reports both a 5-hour and a weekly window, the widget shows the one closer to running out.

The UI is in English with a Russian translation.

## Requirements

- KDE Plasma 5.27 (developed on Kubuntu 24.04).
- The [Codex CLI](https://github.com/openai/codex) on the `PATH` of the Plasma session, logged in with a ChatGPT account (`codex login`).

## Install

Download the `.deb` from [Releases](https://github.com/aadegtyarev/plasma-codex-usage/releases) and install it:

```sh
sudo apt install ./plasma-codex-usage_*_all.deb
```

Then add **Codex Usage** to a panel (right-click the panel → Add Widgets). If Plasma does not list it yet, restart Plasma or log out and back in.

## How it works

`codex-usage` (installed to `/usr/bin`) starts `codex app-server`, asks it for `account/rateLimits/read` — the same data Codex shows in `/status` — and prints one line of JSON:

```sh
$ codex-usage
{"remainingPercent": 70, "windowMinutes": 10080, "resetsAt": 1796097689, "freeResets": 2}
```

On failure it prints `{"error": "<code>"}` and exits with 1; the widget turns the code into text.

Codex handles the login and token refresh itself, so no credentials are read or stored by this project. The widget runs `codex-usage` once a minute; each run takes about a second and roughly 0.5 s of CPU time, and nothing stays in memory between runs.

## Development

```sh
python3 -m unittest discover -s tests -v
```

The tests use a fake `codex app-server` and also check that `po/*.po` match the strings in the QML. To add a language, copy `po/ru.po` to `po/<language>.po` and translate the `msgstr` lines.

GitHub Actions builds the `.deb` on every push and attaches it to a release for `v*` tags.

## Disclaimer

OpenAI, ChatGPT and Codex are trademarks of OpenAI. This is an independent, unofficial project; it is not affiliated with, endorsed by or supported by OpenAI. The OpenAI logo (from Simple Icons, CC0) is used only to identify the service the widget reports on.

## License

MIT, see [LICENSE](LICENSE).
