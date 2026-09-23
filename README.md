![Dwelf Cat](/dwelf.jpg)

# dwelf.py — Dell Website Equipment Link Finder

A command-line scraper for Dell's support site (drivers, manuals, articles,
videos, advisories, regulatory documents) for a given Dell product — by
model name, a direct URL, or a service tag.

## Version

**0.4.2** — see `CHANGELOG.md` for the full version history. This section
is kept in sync with `__version__` in `dwelf.py`; run `python3 dwelf.py
--version` to confirm what you actually have installed.

## Example Usage

```
❯ python3 dwelf.py --model R630
[
  {
    "name": "Dell Server PowerEdge BIOS R630/R730/R730XD Version 2.19.0",
    "category": "BIOS",
    "release_date": "18 Mar 2024",
    "importance": "Urgent",
    "download_url": "https://dl.dell.com/FOLDER11275682M/1/BIOS_KM6P8_LN64_2.19.0.BIN"
  }
]
```

## Why this isn't a simple `requests`/`curl` script

Dell's support site renders its content client-side and fronts everything
with Akamai bot management, which returns a hard `403 Access Denied` to
typical scripted requests. `dwelf.py` drives a real, visible browser
(non-headless by default) via Selenium instead — this reliably gets past
Akamai's protection in testing, in a way headless mode and plain HTTP
requests do not. See [Known limitations](#known-limitations) below for the
specifics, and `CHANGELOG.md` for the full story of what was tried and
confirmed along the way.

## Requirements

```
pip install -r requirements.txt
```

(The script also auto-installs any of these it finds missing at runtime,
via `pip install`, so this step is optional — but running it up front
avoids that happening mid-run.)

You also need **Google Chrome or Chromium installed** (Selenium's built-in
"Selenium Manager" downloads a matching chromedriver automatically):

```
sudo apt install chromium-browser   # or: google-chrome-stable
```

**Do not rely on Ubuntu's default `chromium` snap package** — it cannot be
automated (its sandboxing breaks Selenium). If `google-chrome-stable`
isn't available either, download Google Chrome's `.deb` directly from
Google.

### Optional: Firefox engine (`--engine firefox`)

Confirmed by testing to get past Akamai on at least one URL that blocked
Chrome outright. Needs a **non-snap** Firefox + geckodriver (Ubuntu's
default `firefox` is also a snap package that cannot be automated at all):

```bash
curl -sL -o /tmp/firefox.tar.xz 'https://download.mozilla.org/?product=firefox-latest&os=linux64&lang=en-US'
tar xf /tmp/firefox.tar.xz -C /tmp
curl -sL -o /tmp/geckodriver.tar.gz https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-linux64.tar.gz
tar xf /tmp/geckodriver.tar.gz -C /tmp && chmod +x /tmp/geckodriver
```

Auto-detected if already on `PATH` (and not a snap); otherwise pass
`--firefox-binary`/`--geckodriver-binary` explicitly.

### `--engine uc` (undetected-chromedriver, the default)

Already covered by `requirements.txt` above. Patches the chromedriver
binary itself to remove automation fingerprints. This is the **default**
engine; use `--engine selenium` for plain Selenium/Chrome with no extra
dependency.

### Running unattended (no display)

Non-headless Chrome needs a real or virtual X display, and `--headless`
gets blocked by Dell's site (see below) — so use Xvfb instead, confirmed
working end-to-end:

```
sudo apt install xvfb
xvfb-run -a python3 dwelf.py --model R630
```

## Usage

One of `--model`, `--url`, or `--servicetag` is required — running with
none of them prints usage and exits.

```bash
# Basic: PowerEdge R630 BIOS drivers (the defaults: --type drivers, --category BIOS, --os BIOS)
python3 dwelf.py --model R630

# Other product types
python3 dwelf.py --model R630 --type manuals              # Manuals & Documents
python3 dwelf.py --model R630 --type articles              # KB Articles (capped at 30, signed-out)
python3 dwelf.py --model R630 --type videos                 # Videos
python3 dwelf.py --model R630 --type advisories --impact High   # Security advisories, High impact only
python3 dwelf.py --model R630 --type regulatory             # Regulatory compliance documents

# Filtering
python3 dwelf.py --model R630 --category Firmware --os "Windows Server 2019 LTSC"
python3 dwelf.py --model R630 --os none                      # leave Dell's default OS selection alone
python3 dwelf.py --model R630 --type manuals --search "release notes"   # post-filter by any field

# Alternative ways to target a product
python3 dwelf.py --url <a product's page URL> --category BIOS   # instead of --model
python3 dwelf.py --servicetag 1MJ4LG2                            # resolve a real tag (intermittent, see below)
python3 dwelf.py --geturl --model R630 --type manuals            # just print the constructed URL, no browser

# Output
python3 dwelf.py --model R630 --output drivers.csv
python3 dwelf.py --model R630 --display text                      # human-readable stdout instead of JSON
python3 dwelf.py --model R630 --download                          # also fetch each file into $HOME/firmware/r630
python3 dwelf.py --model R630 --download --directory /path/to/dir

# Browser engine / troubleshooting
python3 dwelf.py --model R630 --debug              # dump screenshots/HTML at each step
python3 dwelf.py --model R630 --engine selenium    # plain Selenium instead of the uc default
python3 dwelf.py --model R630 --engine firefox     # Firefox instead of Chrome
python3 dwelf.py --model R630 --chrome-binary /path/to/chrome
xvfb-run -a python3 dwelf.py --model R630          # unattended, no display available
```

## Flag reference

| Flag | Default | Purpose |
|---|---|---|
| `--model MODEL` | — | Dell model name, e.g. `R730`, `"Dell Precision Tower 3420"`. See [Supported product lines](#supported-product-lines-for---model). |
| `--url URL` | — | A full Dell product-support URL, instead of `--model`. |
| `--servicetag TAG` | — | Resolve a real service tag to a product instead of guessing `--model`. Intermittent — see [Known limitations](#known-limitations). |
| `--geturl` | off | Print the constructed URL and exit — no browser, no network. Not compatible with `--servicetag`. |
| `--type TYPE` | `drivers` | `drivers`, `manuals` (alias `documents`), `articles`, `videos`, `advisories`, `regulatory`. |
| `--locale LOCALE` | `en-au` | Locale segment of the URL, e.g. `en-us`. |
| `--category`, `--cat` | `BIOS` | Driver category filter (only applies to `--type drivers`). |
| `--os OS` | `BIOS` | Operating System filter (`drivers` only). `--os none` leaves Dell's default alone. |
| `--impact IMPACT` | — | `Critical`/`High`/`Medium`/`Low` filter (`--type advisories` only). |
| `--search TEXT` | — | Post-filter: keep only results containing this string in any field. |
| `--output FILE` | stdout | Write results to `.json` or `.csv` instead of printing. |
| `--display {json,text}` | `json` | Stdout rendering format only — `--output` always writes JSON/CSV regardless. |
| `--download` | off | Also fetch each result's linked file into `--directory`. |
| `--directory DIR` | `$HOME/firmware/<model>` | Destination for `--download`. |
| `--headless` | off | Run the browser headless. **Reliably blocked by Dell** — see below. |
| `--engine {uc,selenium,firefox}` | `uc` | Browser automation backend. |
| `--chrome-binary`, `--firefox-binary`, `--geckodriver-binary` | auto-detect | Explicit binary paths if auto-detection fails. |
| `--debug` | off | Show verbose `[+]` progress on stderr and save numbered screenshot/HTML dumps at each stage. |
| `--version` | — | Print the script name, full name, and version. |

Run `python3 dwelf.py --help` for the complete, up-to-date text.

## Supported product lines for `--model`

`--model` accepts a plain model number (assumed PowerEdge) or a descriptive
name, normalized into Dell's actual URL slug. Each rule below was
confirmed by testing the resulting URL against the real site:

| Input | Resulting slug | Rule |
|---|---|---|
| `R630` | `poweredge-r630` | Bare number, no product line named → assumed PowerEdge. |
| `Dell Precision Tower 3420` | `precision-t3420-workstation` | Tower → `t` prefix. |
| `Dell Precision Compact 3260` | `precision-3260-workstation` | Compact → no prefix letter. |
| `Dell Optiplex 3000 Micro` | `optiplex-3000-micro` | Unrecognized form factor word → left as-is. |
| `OptiPlex 3040 Small Form Factor` | `optiplex-3040-sff` | Recognized form factor → abbreviated. |
| `Latitude 3460` | `latitude-3460-laptop` | Laptop-only line → `-laptop` always appended. |
| `XPS 13 9340` | `xps-13-9340-laptop` | Two number tokens → laptop. |
| `XPS 8940` | `xps-8940-desktop` | One number token → desktop tower. |
| `Inspiron 15 3530` | `inspiron-15-3530-laptop` | Same token-count rule as XPS. |
| `Inspiron 24 5410 All-in-One` | `inspiron-24-5410-aio` | Explicit word **overrides** the token-count rule. |

Other product lines (or Precision/OptiPlex/Inspiron variants not listed
above) aren't specially handled yet and will likely produce a wrong slug.
Use `--geturl` to check the constructed URL before a full run, or pass
`--url`/a full correct slug directly via `--model` if you already know it.

## Known limitations

- **`--headless` is reliably blocked** by Dell's Akamai bot protection,
  with every engine tested (plain Selenium, `uc`, Firefox). Non-headless
  (including under Xvfb, which is a real render target, just off-screen)
  is the only confirmed-working mode.
- **`--servicetag` is intermittent.** Its lookup hits a backend endpoint
  Akamai protects separately and more aggressively than the pages
  themselves — most automated attempts get silently blocked with no
  visible error; occasionally an interactive "I'm not a robot" challenge
  appears instead, which `dwelf.py` attempts to solve automatically.
  Switching `--engine` does not reliably help here (unlike for page
  loading in general).
- **`--type articles`** returns at most 30 results for a signed-out
  session, even if more exist — Dell requires a Dell account to see more.
- **`--type advisories`** only returns the "Security" tab; "Technical"
  advisories aren't fetched (loaded lazily on click, not on page load).
- **`--download`** works well for direct file links (drivers, regulatory
  PDFs — typically hosted on `dl.dell.com`, which isn't behind Akamai's
  page-level protection), but a result whose only link is a
  `www.dell.com` webpage (advisories, articles, some manuals, videos)
  will likely fail the same way plain `curl`/`requests` do against Dell's
  pages generally.

## Troubleshooting

- **`SessionNotCreatedException` / chromedriver version mismatch**: your
  installed Chrome and the auto-downloaded chromedriver have drifted out
  of sync (more likely with `--engine uc`, which manages its own driver
  download). Update Chrome, or try `--engine selenium`.
- **Chrome/Firefox crashes immediately, or "profile cannot be loaded"**:
  you're likely running the distro's snap-packaged browser. Install a
  real (non-snap) Chrome/Chromium or Firefox — see
  [Requirements](#requirements).
- **No DISPLAY found**: run under `xvfb-run -a` (see
  [Running unattended](#running-unattended-no-display)), or pass
  `--headless` (not recommended — reliably blocked by Dell).
- **`--debug`** is your friend for anything else: it shows verbose `[+]`
  step-by-step progress and dumps a numbered screenshot + HTML file at
  every stage, so you can see exactly what the browser saw. Normal runs
  are quiet by default (just the result output) — this is what turns the
  chatter back on.

## Full change history

See `CHANGELOG.md` for the complete, versioned history of every feature,
bug, and thing confirmed (or ruled out) by testing along the way.

## License

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-nc-sa/4.0/)
(CC BY-NC-SA 4.0).

You are free to share and adapt this work for non-commercial purposes,
with attribution, as long as you distribute any adaptations under the
same license. See the linked license for the full terms.
