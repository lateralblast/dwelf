# Changelog

All notable changes made to `dwelf.py` during development, in the
order they actually happened, each as its own version starting at 0.0.1.

## [0.0.1] - Initial script

- Selenium-based scraper for the PowerEdge R630 Drivers & Downloads page,
  filtering by Category (default `BIOS`).
- CLI flags: `--url`, `--category`, `--no-headless`, `--debug`, `--output`.
- Used `undetected-chromedriver` as the browser backend.

## [0.0.2] - Switch to plain Selenium

- Dropped `undetected-chromedriver` for `build_driver()` after it crashed
  with `TypeError: Binary Location Must Be a String` - root cause was no
  real Chrome/Chromium binary present (the `chromium` on the test machine
  was a snap package, whose sandboxing also broke Selenium automation
  independently of that error).
- Added `find_chrome_binary()` auto-detection and `--chrome-binary` to
  point at an explicit binary, with a clear error message instead of a
  cryptic crash when none is found.

## [0.0.3] - Progress logging and staged debug dumps

- Fixed the script appearing to hang with no feedback: original per-stage
  waits could silently stack up to ~80s with zero output. Added
  `progress()` logging at every stage and shortened per-stage timeouts.
- Added numbered `--debug` screenshot + HTML dumps at each stage (page
  load, after cookie banner, after content render, after each filter,
  final state) to diagnose selector breakage against the real page.

## [0.0.4] - Real Category filter and results grid

- Replaced the initial guess-based CSS/XPath selectors (written before any
  real page had been inspected) with selectors built from an actual live
  DOM capture: Dell's "DDS" component library uses a combobox pattern for
  the Category filter (`dnd-cat-dropdown-*`) and an ARIA grid
  (`div.dds__tr[data-row]` / `[role='gridcell']`) for driver results.

## [0.0.5] - `--os` flag

- Added `--os` (default `BIOS`) to also filter by Operating System before
  scraping (Dell exposes "BIOS" as an OS-agnostic bucket for BIOS/firmware
  updates alongside real OS choices). `--os none` leaves Dell's own default
  OS selection untouched.
- Refactored the single `select_category()` clicking logic into a shared
  `select_dropdown_option()`, since Category and Operating System turned
  out to share the same underlying combobox markup.

## [0.0.6] - Fix OS dropdown close crash

- Fixed `ElementNotInteractableException` when closing the Operating
  System dropdown after selecting an option: single-select dropdowns
  auto-close on selection (unlike multi-select Category), leaving the
  trigger briefly non-interactable. Made the "close the dropdown" step
  (`close_dropdown()`) best-effort/non-fatal for both dropdown types.

## [0.0.7] - `--model` flag

- Added `--model` (default `R630`) and `build_product_url()` to build the
  target URL for other PowerEdge models (`R730`, `poweredge-r730`,
  `PowerEdge R730` all normalize the same way) instead of hardcoding the
  R630.

## [0.0.8] - `--type` and `--locale` flags

- Added `--type` (default `drivers`) and `TYPE_URL_TEMPLATES`, since Dell
  uses different URL shapes for different product-support pages
  (`support/home/...` for drivers vs. `support/product-details/...` for
  others). Introduced `manuals` as the second supported type.
- Added `--locale` (default `en-au`) for the locale segment of the URL.

## [0.0.9] - Manuals scraping

- Implemented `ManualInfo` / `scrape_manuals()` / `scrape_manuals_page()`
  for `--type manuals`, built from the real captured DOM
  (`#manualsdetails` list, no filtering).

## [0.1.0] - Default to non-headless

- Flipped the default from headless to non-headless
  (`--headless` now opts in). Dell's Akamai bot protection reliably
  blocks headless Chrome outright - confirmed by testing, not assumed.

## [0.1.1] - Auto-install missing dependencies

- Added `ensure_package()`: tests an import and runs `pip install` before
  re-importing, instead of failing outright on `ImportError`. Applied to
  `selenium` at module load.

## [0.1.2] - `--engine uc` option

- Reintroduced `undetected-chromedriver` as an opt-in `--engine uc`
  backend (`build_driver_uc()`) alongside the default `selenium` engine,
  now that a real Chrome binary and `setuptools` (see below) were in
  place. `ensure_package()` extended to also auto-install
  `undetected-chromedriver` and its `setuptools` prerequisite (the
  `distutils` shim Python 3.12+ needs) when `--engine uc` is used.
- Confirmed testing that `--headless` is blocked by Dell's Akamai
  protection with either engine - not just plain Selenium.

## [0.1.3] - Xvfb support for unattended runs

- Added `check_display_available()`: since this script defaults to
  non-headless Chrome, running it on a display-less server used to crash
  inside Chrome with a cryptic error. It now raises a clear error pointing
  at `xvfb-run -a python3 dwelf.py ...` instead.
- Confirmed working end-to-end under `xvfb-run`, including in combination
  with `--model`/`--type`.

## [0.1.4] - `--type documents` alias

- Added `documents` as an alias for `manuals` (`TYPE_ALIASES`,
  `normalize_type()`), resolved once at the CLI boundary so it flows
  through URL-building, dispatch, and error messages consistently.

## [0.1.5] - `--type articles`

- Implemented `ArticleInfo` / `scrape_articles()` / `scrape_articles_page()`
  for `--type articles`, built from the real captured DOM
  (`#articlesisgdetails` list).
- Discovered and documented that Dell caps the public/signed-out view at
  30 rows even when more exist (confirmed by testing that the "Show More"
  button doesn't add rows without a Dell account); the script returns that
  same public batch rather than faking full pagination.

## [0.1.6] - `--type videos`

- Implemented `VideoInfo` / `scrape_videos()` / `scrape_videos_page()` for
  `--type videos`, built from the real captured DOM (`#videodetails` card
  grid).
- Confirmed (unlike articles) that all cards are already present in the
  DOM on load - "Show More" here only toggles CSS visibility - so the full
  list is returned with no cap.

## [0.1.7] - `--type advisories`

- Implemented `AdvisoryInfo` / `scrape_advisories()` /
  `scrape_advisories_page()` for `--type advisories`, built from the real
  captured DOM (`#table-adv-product` grid, excluding paired collapsed
  `.dds__tr__expandable` detail rows).
- Discovered and documented that only the default "Security" tab is
  populated on load; the "Technical" tab (`#table-adv-product-eta`) stays
  an empty `<div>` until clicked, so only Security advisories are
  returned.

## [0.1.8] - `--impact` flag

- Added `--impact` (default unset - returns all advisories), used with
  `--type advisories` to filter by Impact (`Critical`, `High`, `Medium`,
  `Low`) via `select_impact()`.
- Discovered the Impact filter's trigger/popup element ids are randomly
  regenerated per page load (unlike Category/OS), so they're resolved at
  runtime from the `<label>` reading "Impact" instead of being hardcoded.
- Discovered the Impact filter doesn't apply live like Category/OS do; it
  requires clicking a separate "Apply" button (`#esaFilterSubmitBtn`).
- Fixed a bug found while testing this: `select_dropdown_option()`'s
  Escape-to-close step, harmless for Category/OS, was clearing the
  tentative Impact selection before Apply could see it, so the filter
  silently had no effect. Added a `close_after` parameter so this step can
  be skipped for comboboxes (like Impact) that use a separate Apply
  button, confirmed fixed by testing (`--impact High` now correctly
  returns 9 of 12 advisories instead of all 12).

## [0.1.9] - `--type regulatory`

- Implemented `RegulatoryInfo` / `scrape_regulatory()` /
  `scrape_regulatory_page()` for `--type regulatory`, built from the real
  captured DOM (`#rdocdetail` list). Fields are parsed by label prefix
  ("Regulatory Model:"/"Regulatory Type:") rather than position, since the
  metadata line's shape isn't as fixed as other page types'.
- Fixed an over-counting bug found while testing: a sibling "N out of N
  shown" counter div matches the same `div.dds__col--lg-12` selector as
  real entry rows (it just lacks their `.dds__mb-2` class), so
  `find_regulatory_rows()` counted one extra row that `scrape_regulatory()`
  then correctly skipped (no link inside it) - fixed by requiring
  `.dds__mb-2` in `REGULATORY_ROW_SELECTOR`, confirmed by testing that the
  reported and actual counts now match (1, not 2, for the R630).

## [0.2.0] - `--search` flag

- Added `--search` (default unset - returns everything scraped): keeps
  only results with the given string (case-insensitive) in any field's
  value via `filter_by_search()`, applied after scraping and after any
  `--type`/`--category`/`--os`/`--impact` filtering already narrowed the
  results. Works identically across every result type (`DriverInfo`,
  `ManualInfo`, `ArticleInfo`, `VideoInfo`, `AdvisoryInfo`,
  `RegulatoryInfo`) since it just inspects a scraped dataclass's field
  values directly, rather than needing a dedicated selector for each
  page's own "Filter by keyword" box.
- Confirmed by testing against `--type manuals`: `--search "release
  notes"` correctly narrowed 22 results to the 3 whose title contains it.

## [0.2.1] - `--servicetag` flag

- Added `--servicetag` (overrides `--model`/`--url`): resolves a real
  service tag to a product via Dell's support home page's "Identify a
  product" search box (`#homemfe-dropdown-input`, id confirmed stable
  across sessions), then builds the normal `--type` URL from the resolved
  product slug via `resolve_service_tag_slug()`, so it can be used with
  every existing flag exactly like `--model` can.
- Discovered by testing (browser console logs) that this lookup calls a
  separate backend endpoint (`/support/assetdiscovery/.../validate/asset`)
  that Akamai protects independently and more aggressively than the page
  itself: most automated attempts get a silent 403 with no visible
  feedback at all, and occasionally an interactive "I'm not a robot"
  checkbox challenge appears instead - a real Akamai Bot Manager
  interstitial served through a same-origin iframe (id observed as
  `sec-cpt-if`), which `try_solve_akamai_challenge()` detects and clicks
  through automatically (confirmed working when the challenge does
  appear, including resubmitting the search afterwards).
- **Confirmed working but intermittent**: `resolve_service_tag_slug()`
  retries the whole lookup (fresh page load) up to 3 times, but a live
  end-to-end test still exhausted all 3 attempts with a silent block each
  time (no challenge shown) - roughly consistent with informal testing
  showing the interactive challenge appearing on the order of 1 in 8
  attempts and a silent block otherwise, with no confirmed clean success
  (no challenge at all) observed in this environment. Success rate may
  differ by network/session. On exhausting all attempts, raises a clear
  error suggesting the user retry or resolve the tag manually once and
  use `--model` instead.

## [0.2.2] - Fix `--servicetag` challenge detection and a crash

- Corrected 0.2.1's claim that the Akamai challenge was "confirmed
  working" when it appears: a user hit the real challenge on a live run,
  but the log showed `try_solve_akamai_challenge()` never detected it -
  the selector targeting one specific iframe id observed during
  development (`sec-cpt-if`) doesn't match every variant of Akamai's
  challenge markup. Replaced it with a brute-force check (top-level
  document, then every iframe on the page, no id/title assumptions).
- Fixed a crash introduced by that broadening: an unrelated, hidden
  checkbox elsewhere on Dell's page also matched the (now wider)
  `//input[@type='checkbox']` search, and clicking it raised
  `ElementNotInteractableException`, killing the whole run. Found by
  testing the broadened detection immediately after writing it. Fixed by
  only considering visible (`is_displayed()`) checkboxes/buttons and
  catching click failures instead of propagating them.
- Added `--debug` screenshot/HTML capture inside `resolve_service_tag_slug()`
  itself (previously only the post-resolution scraping had debug dumps,
  so the lookup step that actually needs diagnosing had none): one dump
  right after submitting each attempt, one right before giving up on it.
- Still no fully confirmed end-to-end success (challenge solved and a
  service tag actually resolved to a product) as of this version - two
  more live attempts after this fix both hit the same silent block with
  no challenge shown, consistent with most prior attempts.

## [0.2.3] - Require an explicit product identifier

- Removed `--model`'s implicit `R630` default. Previously, forgetting
  `--model`/`--url`/`--servicetag` entirely silently scraped the R630
  without any indication that no product was actually specified.
- Running with none of `--model`/`--url`/`--servicetag` now prints usage
  and exits (code 2) instead. Removed the now-unused `DEFAULT_MODEL`
  constant.

## [0.2.4] - Fix `--model` normalization for messy whitespace

- `--model "PowerEdge R630"` (a descriptive name with a single space)
  already normalized correctly to `poweredge-r630` - confirmed by testing
  before making any change.
- Found and fixed a real bug while verifying that: `model.strip().lower().
  replace(" ", "-")` only collapsed single spaces, so `"PowerEdge  R630"`
  (double space) or `"PowerEdge - R630"` produced a broken slug like
  `poweredge--r630`. Replaced with a regex that collapses any run of
  whitespace and/or hyphens into one, confirmed by testing against both
  of those cases plus `"R630"`, `"poweredge-r630"`, and leading/trailing
  whitespace.

## [0.2.5] - `--engine firefox`

- Added `--engine firefox` (plus `--firefox-binary`/`--geckodriver-binary`
  overrides): drives Firefox instead of Chrome entirely, via
  `build_driver_firefox()`.
- **Confirmed by testing to be a real, meaningful improvement**: a URL
  that was reliably blocked with a hard 403 by Dell's Akamai protection
  using Chrome - both plain Selenium and undetected-chromedriver - loaded
  correctly via Firefox in the same environment, with a full driver scrape
  (Category/OS filters, result grid) working end-to-end. Likely because
  Akamai's bot-detection models are tuned mostly against Chrome-based
  automation (Selenium/Puppeteer/Playwright overwhelmingly target Chrome).
- Found and fixed the same class of problem `--engine uc` hit earlier, but
  worse: Ubuntu's default Firefox is *also* a snap package, and testing
  showed it cannot be automated **at all** (not just "less reliable" like
  snap Chromium) - its confinement blocks Firefox from accessing the
  profile directory Selenium/geckodriver create outside the snap's own
  sandboxed paths, failing with "Your Firefox profile cannot be loaded" or
  "Process unexpectedly closed with status 1" regardless of which
  geckodriver is paired with it. A snap `geckodriver` wrapper on PATH
  compounds this: it only accepts the snap's own bundled Firefox, so even
  a correctly-installed standalone Firefox fails with "binary is not a
  Firefox executable" if that wrapper is what gets picked up.
- `find_firefox_binary()`/`find_geckodriver_binary()` detect and skip
  snap-confined paths - found by testing that a naive `realpath()` check
  (which worked for detecting snap Chromium) misses both of Firefox's
  indirection styles: `/usr/bin/firefox` is a real (non-symlink) shell
  script whose realpath is itself, and `/snap/bin/geckodriver`'s realpath
  resolves to `/usr/bin/snap` (the generic launcher), neither of which
  contains "/snap/" as a path component. Fixed with a combined check: the
  original path, its realpath, and (for shell-script wrappers) the
  script's own content.
- Tested against the real motivating case (`--servicetag`) too: it does
  **not** meaningfully help there. That lookup's backend endpoint still
  gets silently blocked most of the time via Firefox as well, suggesting
  it carries its own separate, stricter, less browser-fingerprint-
  dependent protection. Updated `resolve_service_tag_slug()`'s error
  message, which had prematurely suggested `--engine firefox` might help,
  to reflect this.
- Documented the standalone (non-snap) Firefox + geckodriver install
  method (Mozilla's official tarball + a GitHub geckodriver release) in
  the module docstring, verified working end-to-end by both the developer
  and a user independently.

## [0.2.6] - `--type downloads` alias

- Added `downloads` as an alias for `drivers` (`TYPE_ALIASES`), following
  the same pattern as `documents`/`manuals`. Verified `build_product_url()`
  produces an identical URL for both, and a full end-to-end scrape via
  `--type downloads` returns the same result as `--type drivers`.

## [0.2.7] - `--download` and `--directory` flags

- Added `--download`: actually fetches each result's file
  (`download_url` if present, else `url`) via `download_results()` /
  `download_file()` (stdlib `urllib`, no new dependency), in addition to
  the usual JSON/CSV output. Off by default - a normal run's behavior is
  unchanged unless `--download` is explicitly given.
- Added `--directory` to choose the destination; defaults to
  `$HOME/firmware/<model>` (`default_download_directory()`), where
  `<model>` is `--model` or `--servicetag`, normalized (lowercased,
  whitespace/hyphens collapsed) the same way `--model` is for a URL slug,
  but without the "poweredge-" prefix assumption since this is a local
  folder name, not a Dell URL.
- Confirmed by testing end-to-end (`--model R630 --download`): downloaded
  a real ~14MB BIOS binary from `dl.dell.com` successfully via plain
  `urllib` - notably, no Selenium/browser session was needed for the file
  fetch itself, only for scraping the page to find the URL. This also
  confirms `dl.dell.com` (the file CDN) isn't behind the same Akamai
  protection as the `www.dell.com` pages.
- Documented (not yet tested) that this will likely work less well for
  result types whose only link is a `www.dell.com` webpage rather than a
  direct file (advisories, articles, some manuals, videos) - `download_file()`
  has no special handling for that case and would likely just save
  whatever Akamai's block page returns for those.

## [0.2.8] - Default `--engine` changed to `uc`

- Changed the default browser backend from `selenium` to `uc`
  (undetected-chromedriver) in both the CLI default and `run_scrape()`'s
  own default, so it applies whether the script is run directly or used
  as a library function. `--engine selenium` still works for plain
  Selenium/Chrome with no extra dependency.
- Hit and fixed an unrelated environment issue while verifying this: a
  stale Chrome install (153) against a freshly auto-downloaded
  chromedriver expecting 154 raised `SessionNotCreatedException`. Not a
  code bug - fixed by upgrading Chrome - but confirms `uc` (which
  downloads its own driver) can be more sensitive to browser/driver
  version drift than plain Selenium's own manager. Worth knowing given
  `uc` is now the default: `--engine selenium` is the fallback if a
  similar mismatch ever appears.

## [0.2.9] - Explicit `--directory` creation

- Moved directory creation from inside `download_file()` (implicit,
  per-file, easy to miss reading the code) to `download_results()`
  (explicit, once, before the download loop starts). `--directory` is now
  created up front - including multi-level nonexistent paths - if it
  doesn't already exist.
- Confirmed by testing: a nonexistent single-level directory and a
  nonexistent multi-level nested path (e.g. `/tmp/a/b/c`) are both created
  correctly before the first file is written.

## [0.3.0] - Renamed to `dwelf.py`

- Renamed the script from `dell_drivers.py` to `dwelf.py`. No functional
  change - `argparse`'s `%(prog)s` derives from `sys.argv[0]` automatically,
  so `--version`/usage output picks up the new name with no code change.
  Updated all filename references in the script's own docstring/help text
  and in this changelog.

## [0.3.1] - `--version` shows the expanded name

- Added `__long_name__ = "Dell Website Equipment Link Finder"` (what
  "dwelf" stands for) and included it in `--version`'s output, which now
  reads `dwelf.py (Dell Website Equipment Link Finder) 0.3.1` instead of
  just `dwelf.py 0.3.1`.

## [0.3.2] - `--cat` shorthand

- Added `--cat` as a short alias for `--category` (same `dest`, same
  default). Confirmed by testing: `--cat "Device Firmware"` filters
  identically to `--category "Device Firmware"`.

## [0.3.3] - `--geturl` flag

- Added `--geturl`: prints the constructed URL (from `--model`/`--type`/
  `--locale`, or `--url`) and exits immediately - no browser, no network
  activity. Placed right after `url` is computed in `main()`, before
  `run_scrape()` (where the browser would launch), so it's a pure string
  operation.
- `--servicetag` isn't supported with it (errors out with exit code 1):
  resolving a tag to a URL requires actually querying Dell, which
  contradicts `--geturl`'s no-network guarantee.
- Confirmed by testing: `--geturl --model r630` (default `--type drivers`),
  with an explicit `--type manuals`, and with `--url` passed straight
  through all print the correct URL and exit 0; `--geturl --servicetag ...`
  alone correctly errors instead of guessing.

## [0.3.4] - Non-PowerEdge `--model` support (Precision Tower)

- Added `normalize_model_slug()`, splitting model-to-slug normalization
  out of `build_product_url()` so more product-line-specific rules can be
  added later. Handles Dell Precision Tower `<N>` specially: Dell
  abbreviates "Tower" to "T" and appends "-workstation" for this line
  (`"Dell Precision Tower 3420"` -> `"precision-t3420-workstation"`),
  confirmed by testing the exact resulting URL against the real site.
  Falls back to the original PowerEdge-assuming rule for everything else,
  unchanged.
- Discovered while verifying this that `TYPE_URL_TEMPLATES["drivers"]`'s
  original URL shape (`support/home/{locale}/product-support/product/
  {slug}/drivers`) was never actually special - confirmed by testing
  (Firefox) that navigating there redirects straight to `support/
  product-details/{locale}/product/{slug}/drivers`, which also loads
  correctly when used directly, for both PowerEdge and Precision slugs.
  Simplified `TYPE_URL_TEMPLATES["drivers"]` to that canonical form
  directly, matching every other type's URL family - one less special
  case, and it's what makes non-PowerEdge product lines work at all.
- Confirmed by testing end-to-end: `--model "Dell Precision Tower 3420"`
  scrapes real drivers correctly, and a `--model R630` regression check
  after the template change still returns the identical result as before.

## [0.3.5] - Precision Compact form factor

- Generalized the single hardcoded Precision Tower rule into
  `PRECISION_FORM_FACTOR_PREFIXES`, a lookup table of form-factor word ->
  slug prefix, after discovering Dell doesn't use one consistent rule
  across Precision form factors: `"Dell Precision Compact 3260"` ->
  `"precision-3260-workstation"` (no letter prefix at all), unlike Tower's
  `"t"` prefix - confirmed by testing the exact resulting URL against the
  real site. Unrecognized form-factor words still fall through to the
  generic PowerEdge-assuming rule rather than guessing a prefix.
- Confirmed by testing end-to-end: `--model "Dell Precision Compact 3260"`
  scrapes real drivers correctly, and both the Tower and PowerEdge cases
  still produce identical slugs/URLs after the refactor (no regression).

## [0.3.6] - OptiPlex support, fixed root cause for future product lines

- Discovered and fixed the actual root cause behind needing product-line
  special cases at all: the generic fallback rule assumed *any* model
  string was a bare PowerEdge model number and force-prepended
  `"poweredge-"` unconditionally, e.g. turning `"optiplex-3000-micro"` into
  the wrong `"poweredge-optiplex-3000-micro"`.
- Added `KNOWN_PRODUCT_LINES` and changed the fallback to only prepend
  `"poweredge-"` when the slug doesn't already start with a name in that
  set. `"Dell Optiplex 3000 Micro"` -> `"optiplex-3000-micro"` (no
  prefix/suffix at all, simpler than Precision) confirmed by testing the
  resulting URL against the real site; Latitude/XPS/Inspiron/Vostro/
  Alienware are included too on the reasoning that assuming no prefix for
  a model that already names its own product line is strictly safer than
  force-prepending "poweredge-" to it, even though those specific slugs
  aren't individually confirmed the same way yet.
- Confirmed by testing end-to-end: `--model "Dell Optiplex 3000 Micro"`
  scrapes real drivers correctly, and Precision Tower/Compact and bare
  PowerEdge model numbers all still produce identical slugs after this
  change (no regression).

## [0.3.7] - OptiPlex form-factor abbreviation

- Added `OPTIPLEX_FORM_FACTOR_ABBREVIATIONS` and matching logic in
  `normalize_model_slug()`: `"OptiPlex 3040 Small Form Factor"` ->
  `"optiplex-3040-sff"`, confirmed by testing the resulting URL against
  the real site (verified both `/drivers` and `/overview` resolve
  correctly for this slug).
- Unlike Precision (form factor before the model number), OptiPlex puts
  the number first and the form-factor description after it, so this
  needed its own regex (`optiplex\s+(\w+)\s+(.+)`) rather than reusing
  Precision's pattern.
- Confirmed by testing that this doesn't regress the plain "Micro" case
  from 0.3.6 (`"Dell Optiplex 3000 Micro"` -> `"optiplex-3000-micro"`,
  unabbreviated): "micro" isn't in the abbreviations table, so it falls
  through to the generic rule exactly as before.

## [0.3.8] - Latitude support

- Added a Latitude rule to `normalize_model_slug()`: bare `"Latitude <N>"`
  -> `"latitude-<n>-laptop"`, e.g. `"Latitude 3460"` ->
  `"latitude-3460-laptop"`, confirmed by testing the resulting URL against
  the real site. Simpler than Precision/OptiPlex - no form-factor lookup
  table, since Latitude is laptop-only, so "-laptop" is appended
  unconditionally rather than looked up.
- Scoped the match to a bare model number (anchored to end of string) only
  - anything with extra descriptive words falls through to the generic
    rule rather than guessing "-laptop" still applies, since only the
    plain case has been confirmed.
- Confirmed by testing end-to-end: `--model "Latitude 3460"` scrapes real
  drivers correctly, and every prior product line's slug is still
  unchanged.

## [0.3.9] - XPS support (laptop vs. desktop)

- No example URL was given this time, so the real slug convention was
  discovered empirically via Dell's own "Find your product" search-and-
  click-through on the support home page, rather than guessed: "XPS 13
  9340" -> `xps-13-9340-laptop`, "XPS 8940" -> `xps-8940-desktop`.
- Unlike every other line handled so far, XPS spans both laptops and
  desktop towers with no word in the model name distinguishing them - only
  the number of tokens after "XPS" does (two -> laptop, one -> desktop
  tower), confirmed by testing the resulting URL against the real site for
  two examples of each (XPS 13 9340 / XPS 15 9530 vs. XPS 8940 / XPS 8950).
  Anything else (e.g. an unconfirmed "2-in-1" variant) falls through to
  the generic rule rather than guessing.
- Confirmed by testing end-to-end: `--model "XPS 13 9340"` scrapes real
  drivers correctly, and every prior product line's slug is unchanged.

## [0.4.0] - Inspiron support (token-count rule + word override)

- No example URL was given this time either, so the real slug convention
  was again discovered empirically via Dell's own "Find your product"
  search-and-click-through, testing one example of each naming variety
  found: bare one-number ("Inspiron 3650"), one-number with an explicit
  "Desktop" word ("Inspiron 3020 Desktop"), bare two-number ("Inspiron 15
  3530"), and two-number with "All-in-One" ("Inspiron 24 5410
  All-in-One").
- Found that Inspiron follows the same token-count fallback discovered
  for XPS (one number -> `-desktop`, two -> `-laptop`) - both bare cases
  and the explicit "Desktop" word all confirmed to agree with that rule -
  but an explicit trailing form-factor word can *override* the fallback:
  "24 5410 All-in-One" has two numbers (would be "-laptop" by the token
  rule alone) but is actually `-aio`. Added
  `INSPIRON_TRAILING_FORM_FACTORS` to check for a known trailing word
  first, falling back to the same token-count rule as XPS only when none
  is found.
- Confirmed by testing end-to-end: `--model "Inspiron 15 3530"` scrapes
  real drivers correctly, and every prior product line's slug (including
  XPS's own token-count rule) is unchanged.

## Also along the way

- Renamed the main orchestration function from `get_drivers()` to
  `run_scrape()` and generalized `write_output()` once it needed to handle
  `ManualInfo`/`ArticleInfo`/`VideoInfo`/`AdvisoryInfo` results, not just
  `DriverInfo`.

## Known limitations (current)

- `--headless` (with either engine) is reliably blocked by Dell's Akamai
  bot protection. Non-headless (or non-headless under Xvfb) is the only
  confirmed-working mode.
- `--type articles` returns at most 30 results for a signed-out session
  even if more exist.
- `--type advisories` only returns the "Security" tab.
