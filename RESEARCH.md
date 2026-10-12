# Research

Ideas considered but not built. Outstanding work is in [TODO.md](TODO.md).

## Attaching to a real, running Chrome

**Idea:** Drive a Chrome the user launched with `--remote-debugging-port`
(Selenium `debuggerAddress`) instead of starting a fresh automated one.
Implemented as `--engine attach` in 0.5.3. Tested once in 0.5.4: `--servicetag` still blocked.

**Why it might help:** Akamai still blocks `--servicetag` resolution and
`--specs` in headed mode on every engine. A hand-launched profile with real
history and cookies avoids the fresh-profile and automation-flag tells.

**Open questions:**

- Blocked on one `--servicetag` run, so CDP being attached may still be a tell. Untested: an everyday profile, or driving the page by hand first.
- Is a dedicated `--user-data-dir` profile enough, or does it need to be the
  user's everyday profile (Chrome 136+ blocks the port on that)?

### Tencent BrowserSkill

**Idea:** Use <https://github.com/Tencent/BrowserSkill> (CLI + daemon +
Chrome/Edge extension, MIT) to drive the user's logged-in browser.

**Why it might help:** Same real-profile benefit as attaching, without CDP
debugging flags. Its README makes no bot-protection-bypass claims.

**Open questions:**

- Tried in 0.5.5: still got the Akamai checkbox challenge on the first lookup; the tag resolved after a human ticked it. A repeat lookup soon after the human solve got no challenge at all (0.5.6), so the scripted click is still untested. Answered in 0.5.7: a scripted `bsk click` on the checkbox and Proceed passed in a clean profile. Still open: whether it is reliable across tags/runs, and does the challenge appear less in a long-used profile?
- Would need a new engine shelling out to its CLI, and a desktop browser, so
  no CI/server use.

## Direct `servicetag/<tag>` URLs instead of the lookup widget

**Idea:** Navigate straight to
`https://www.dell.com/support/product-details/{locale}/servicetag/{tag}/{type}`
instead of typing the tag into the overview page's widget.

**Why it might help:** Skips the widget that triggers the silent first-submit
failure and the checkbox challenge. Worked in 0.5.8 via `bsk`.

**Open questions:**

- Answered in 0.5.9 for `uc` and `selenium` (drivers, one tag). Still open: `firefox`, other tags and product lines.
- Answered for `--specs` in 0.6.0 (export downloaded on the direct URL, `uc`).
- `run_scrape` and the cache are keyed on the slug and the
  `--servicetag` label; does the scraper work unchanged on the
  `servicetag/<tag>` URL for every `--type`?

**Update (0.6.4):** worked for drivers, manuals, videos, regulatory and
`--specs`, then Akamai began returning `Access Denied` for the
`servicetag/...` path (both tested tags) while `/product/<slug>/` pages
still loaded. Open: is it rate-based and temporary, and does the fallback
need a slug source that doesn't touch this path?

