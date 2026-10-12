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

## [0.4.1] - `--display` flag

- Added `--display {json,text}` (default `json`, unchanged behavior) to
  control stdout rendering only. `text` renders each result as a
  "Pretty Key: value" block via a new `format_as_text()` (None fields
  omitted). `--output` (writing to a `.json`/`.csv` file) is deliberately
  unaffected by `--display` and keeps its existing behavior exactly - a
  separate flag name was chosen specifically to avoid overloading
  `--output`'s existing meaning (destination path).
- Confirmed by testing: default (no `--display`) output is byte-identical
  to before; `--display text` renders correctly; `--output file.json
  --display text` still writes plain JSON to the file (only stdout, which
  isn't used in that case, would have been affected).

## [0.4.2] - Quiet by default

- The verbose `[+] ...` step-by-step progress lines (`progress()`, 44 call
  sites) now only print when `--debug` is given, via a module-level
  `_DEBUG_ENABLED` flag set from `args.debug` at the top of `main()`.
  Default output is now just the result JSON/text, with none of the
  step-by-step chatter. Errors, warnings ("No results found", etc.), and
  "Wrote N result(s) to FILE" all use plain `print()` elsewhere in the
  script rather than `progress()`, so none of those are affected.
- Updated `--debug`'s help text, which previously undersold it as just
  saving screenshots/HTML - it now also gates the verbose progress output.
- Confirmed by testing: default output for `--model R630` is now just the
  JSON result with no `[+]` lines at all; `--debug` restores the full
  verbose trace and the numbered screenshot/HTML dumps exactly as before.
- Worth knowing: this also quiets some warnings that aren't purely
  cosmetic (e.g. `--download`'s "Skipping/Failed to download" per-file
  notices), which only route through `progress()` too - they're silent
  unless `--debug` is passed.

## [0.4.3] - `--display table`

- Added `table` as a third `--display` option, via a new
  `format_as_table()` using the `terminaltables` package (auto-installed
  on demand via `ensure_package()`, same as every other optional
  dependency in this script). Column headers come from the first result's
  field names, `None` values render as an empty cell.
- Confirmed by testing end-to-end for both a single-row (`--type drivers`)
  and a 22-row (`--type manuals`) result set: renders correctly in both
  cases, and `terminaltables` was confirmed to actually get auto-installed
  rather than assumed already present.
- Added `terminaltables` to `requirements.txt` under its own "--display
  table" section, matching the file's existing per-feature grouping.

## [0.4.4] - `--list` flag

- Added `--list {categories,os,types}` to print available values instead
  of scraping results, then exit. `--list types` is a static list (no
  browser, works with no `--model`/`--url`/`--servicetag` at all);
  `--list categories`/`--list os` need `--model` or `--url` and open that
  product's **drivers** page specifically (forcing `drivers` regardless of
  whatever `--type` was passed, since those dropdowns only exist there) to
  read every live dropdown option, including Dell's live per-option counts
  (e.g. `SAS Drive (107)`).
- Added `list_dropdown_options()`, which opens a Dell DDS combobox and
  collects every option's label text without selecting any of them -
  distinct from the existing `select_dropdown_option()`, which finds and
  clicks exactly one.
- Extracted the `--engine` selection branch out of `run_scrape()` into a
  new shared `build_any_driver()`, used by both `run_scrape()` and the new
  `run_list()`, so `--list` respects `--engine`/`--headless`/binary
  overrides identically to a normal scrape.
- Confirmed by testing end-to-end against the real R630 drivers page:
  `--list categories` returned all 24 real Category options with live
  counts, `--list os` returned all 21 real OS options, and `--list types`
  returned the static type list with no browser launched. Confirmed no
  regression in `--geturl` (still short-circuits before `--list` is
  considered) or a normal `--model R630` scrape.

## [0.4.5] - `--checkconfig` flag

- Added `--checkconfig` to report whether each package in
  `requirements.txt` (`selenium`, `undetected-chromedriver`, `setuptools`,
  `terminaltables`) is importable and which version is installed, then
  exit - no `--model`/`--url`/`--servicetag` needed, and no browser or
  network activity. Exits `0` if `selenium` (the only always-required
  package) is present, `1` otherwise; a missing optional package is
  reported but doesn't fail the check, since `ensure_package()` still
  auto-installs it the first time `--engine uc` or `--display table`
  actually needs it.
- New `check_requirements()` deliberately doesn't call `ensure_package()`
  itself (which would install anything missing) - it uses
  `importlib.util.find_spec()` to check presence and
  `importlib.metadata.version()` to read the installed version, so
  `--checkconfig` is a read-only diagnostic.

## [0.4.6] - `--verbose` flag

- Added `--verbose` to show the same `[+]` step-by-step progress lines
  `--debug` already printed, but without `--debug`'s screenshot/HTML
  dumps at each stage. `--debug` still implies `--verbose`.
- Decoupled `progress()`'s gate from `--debug` specifically: it's now
  driven by a renamed `_VERBOSE_ENABLED` global, set from
  `args.verbose or args.debug` in `main()`. The `debug` parameter threaded
  through `run_scrape()`/`scrape_*_page()` for `save_debug_artifacts()`
  calls is unchanged and still tied only to `--debug`.

## [0.4.7] - Fixed the SERVICE_TAG_BASE_SLUG same-product gap; dismiss feedback popup

- Fixed `resolve_service_tag_slug()` silently failing (3/3 attempts,
  always timing out) for a service tag that belongs to
  `SERVICE_TAG_BASE_SLUG` (`poweredge-r630`) itself - the exact gap the
  code comment above `SERVICE_TAG_INPUT_ID` already documented, now
  confirmed happening in practice with a real tag (`1MJ4LG2`): a `--debug`
  screenshot showed Dell had resolved the tag to the correct product
  (title, Service Tag, and per-tag widgets all rendered) within about 2
  seconds of submitting, but the script kept polling for a URL slug other
  than `poweredge-r630`, which this tag's resolved URL never has, so it
  ran out the full `poll_timeout` on every attempt regardless. Now, when
  the URL slug is still `SERVICE_TAG_BASE_SLUG`, resolution is also
  checked via `document.body.innerText` (through `execute_script()`,
  since the service tag label isn't reliably present in
  `driver.page_source`) for the submitted tag having been echoed back
  into the page - true only once Dell's widget has actually resolved it.
- Added `dismiss_feedback_popup()` (a "We value your feedback!" Qualtrics-
  style survey intercept, confirmed appearing on a real page load by a
  user screenshot mid-session) and call it everywhere
  `dismiss_cookie_banner()` already is, plus once per iteration of
  `resolve_service_tag_slug()`'s poll loop, in case it appears
  mid-wait. Modeled on `try_solve_akamai_challenge()`: checks the
  top-level document, then every iframe, best-effort and non-fatal either
  way.
- **Not fully re-confirmed end-to-end**: after these fixes, `1MJ4LG2` hit
  Akamai's silent block on every one of 6 further attempts in the same
  session (consistent with the already-documented "most attempts fail
  silently" behavior), so the new `document.body.innerText` resolution
  path itself has not yet been observed succeeding against a live
  resolved page. It's a direct, narrowly-targeted fix for the confirmed
  gap above and doesn't change behavior for the normal case (slug differs
  from `SERVICE_TAG_BASE_SLUG`), but treat it as unconfirmed until a
  future run actually exercises it.

## [0.4.8] - On-disk result cache

- Added a cache for scrape results: a successful (non-empty) scrape for
  `--model`/`--servicetag` (not `--url` alone, which has no label to
  cache under) is written as JSON to `--cache-dir` (default
  `$HOME/.dwelf/cache`) under a subdirectory for that `--model`/
  `--servicetag`, normalized the same way `--download`'s default
  `--directory` already is. A later run with the same product, `--type`,
  `--category`/`--os` (`--type drivers`), `--impact` (`--type
  advisories`), and `--locale` reuses the cached file - confirmed by
  testing (`--model R630`) to need no browser launch at all on a cache
  hit (0.4s vs. a full live scrape) - which also means one less real
  request for Akamai to potentially block. `--no-cache` always scrapes
  live and skips writing a new cache file.
- A scrape that comes back with zero results is deliberately never
  cached: `scrape_*_page()` already swallows its own `TimeoutException`
  and returns an empty list either way (see e.g. `scrape_drivers_page()`
  above `select_os()`), so a blocked or never-rendered page is
  indistinguishable from a real "nothing matched" from the result alone -
  caching either would risk permanently hiding a transient block behind a
  false empty answer.
- Extracted `normalize_label()` out of `default_download_directory()`
  (unchanged behavior) so the cache's per-product directory name and
  `--download`'s default directory name are normalized identically -
  confirmed by testing that `cache_file_path()` produces distinct,
  filesystem-safe paths for a plain model number, a real service tag, and
  a multi-word descriptive model name.
- New `--type`/`--category`/`--os`/`--impact`/`--locale` combinations
  cache to separate files by design (`cache_file_path()`), so switching
  filters on the same product never reads stale results from a different
  filter by mistake.

## [0.4.9] - `--specs` flag; fixed a crash in the Akamai-challenge resubmit path

- Added `--specs` (requires `--servicetag`, not `--model`/`--url`):
  resolves the tag, clicks "Product Specifications" on its resolved
  overview page, clicks through to export it, and saves the download to
  `--cache-dir`'s `<servicetag>/specs.<ext>`, printing its path. A cached
  file from an earlier run is reused as-is, with no live site access at
  all, same as the result cache added in 0.4.8 - `--no-cache`/
  `--cache-dir` apply here too.
- `--specs` requiring `--servicetag` isn't an arbitrary restriction:
  confirmed by testing that "Product Specifications" only appears in
  Quick Links on a *resolved* overview page - neither the plain,
  not-yet-identified `SERVICE_TAG_BASE_SLUG` overview page nor a
  `--model`-style direct overview page for a different product
  (`poweredge-r730`, tested directly) shows it.
- Added `download_dir` support to `build_driver()`/`build_driver_uc()`/
  `build_driver_firefox()` (Chrome: prefs plus a `Page.setDownloadBehavior`
  CDP call for reliability; Firefox: `browser.download.dir` plus disabling
  `pdfjs` so a PDF downloads instead of opening in Firefox's inline
  viewer), so a browser built for `--specs` saves straight into the cache
  label directory instead of prompting or opening the file inline.
- New `click_first_visible()`, `click_link_by_text()` (PARTIAL_LINK_TEXT
  first, then an XPath text-match fallback, optionally scoped to a root
  element's subtree), and `wait_for_download()` (polls a directory for a
  new, no-longer-`.crdownload`/`.part` file) are the pieces `run_specs()`
  is built from.
- **Selectors confirmed against a real resolved overview page's saved
  HTML** (a user supplied a copy, since Dell's Akamai bot protection
  blocked every further `1MJ4LG2` resolution attempt made while writing
  this feature - see below): "Product Specifications" is
  `<a id="review-specs-drawer-trigger" href="javascript:void(0)">`,
  wired to a same-page DDS slide-out drawer (`id="review-specs-drawer"`,
  `class="dds__drawer"`, `aria-hidden="true"` when closed), not a new
  page or tab as first assumed - `run_specs()` was rewritten around this
  (`click_first_visible()` for the trigger, since its id is duplicated
  across responsive breakpoints and only one copy is ever visible;
  waiting on the drawer's `aria-hidden` before looking for the export
  control inside it, scoped via `click_link_by_text()`'s new `root`
  param). The drawer's content (including its export control) is fetched
  only once opened (`ReviewSpecs.init()`), so it's genuinely absent from
  the static markup - not fully confirmed, but the same user's export of
  this same drawer downloaded a `.csv` (a parts/BOM listing), which is
  why `SPECS_EXPORT_LINK_TEXTS` now tries `"Export"`/`"Export CSV"`/
  `"Download"` instead of the earlier, wrong PDF-flavored guesses.
- **Still not confirmed end-to-end live.** Offline testing (loading the
  saved overview page via a `file://` URL) confirmed `click_first_visible()`
  finds and clicks the real trigger element without error, but the page's
  own JavaScript (an external DDS bundle) never executed in that static
  snapshot, so the drawer never actually opened there either - this
  validates the selector and the click, not the resulting drawer-open/
  export behavior. Getting to a resolved `--servicetag` at all remains
  the same code path confirmed working in 0.4.7, but Dell's Akamai bot
  protection blocked every further `1MJ4LG2` resolution attempt made
  while writing this feature - most attempts timed out silently, and the
  ones that got as far as an "I'm not a robot" challenge kept
  re-presenting it repeatedly (confirmed by testing: the same challenge
  was solved and re-shown 6+ times in a row within a single attempt).
  Treat the drawer-open and export steps as unconfirmed until a future
  run with a less-challenged session actually reaches them live;
  `--debug`'s `dell_debug_specs_*` dumps are the intended way to fix them
  if they're wrong.
- Fixed a real, previously-crashing bug hit while testing the above:
  `resolve_service_tag_slug()`'s post-challenge resubmit
  (`submit_tag()`) only caught `NoSuchElementException`, but a click
  right after solving a challenge can still land on the challenge
  iframe mid-teardown, raising `ElementClickInterceptedException`
  instead and crashing the whole script with a traceback - confirmed
  happening in practice (reproduced twice). Now also caught, and a
  2-second wait was added before the resubmit to make hitting it less
  likely in the first place.

## [0.5.0] - `--specs` renders a cached/downloaded CSV as a table

- `--specs` now reads a `.csv` result (cached or freshly downloaded) with
  new `read_csv_rows()` and prints it via the existing `format_as_table()`
  (the same rendering `--display table` uses), instead of only ever
  printing the file's path. A non-`.csv` result, or a `.csv` with no data
  rows, still falls back to printing the path, unchanged from 0.4.9.
- `read_csv_rows()` opens with `encoding="utf-8-sig"`, not plain `utf-8`:
  confirmed by testing against a real downloaded specifications CSV
  (from a user) that Dell's export includes a UTF-8 BOM, which corrupted
  the first column's header (`"﻿Component"` instead of `"Component"`)
  before this fix.

## [0.5.1] - `normalize_label()` preserves case

- `normalize_label()` (the shared path-component normalizer behind the
  on-disk cache directory, `--specs`'s `<servicetag>/specs.<ext>`, and
  `default_download_directory()`'s `$HOME/firmware/<model>`) no longer
  lowercases its input, only collapsing whitespace/hyphens. A service tag
  like `1MJ4LG2` and a model like `R630` now keep their original case
  everywhere on disk, matching how Dell itself displays them, instead of
  being written as `1mj4lg2`/`r630`. Existing lowercase cache directories
  on this machine (`~/.dwelf/cache/1mj4lg2` - empty, removed;
  `~/.dwelf/cache/r630` -> `R630`; `~/firmware/r830` -> `R830`) were
  migrated by hand to match. The lowercase URL-slug rule `--model` itself
  uses to build a Dell URL (a separate function) is unrelated and
  unchanged, since Dell's own URLs require lowercase.

## [0.5.2] - `--specs` cache filename uses the service tag, not `specs.<ext>`

- `run_specs()` now saves an exported result as
  `<cache_dir>/<servicetag>/<servicetag>.<ext>` (e.g.
  `1MJ4LG2/1MJ4LG2.csv`) instead of `<servicetag>/specs.<ext>`, and
  `find_cached_specs()`'s glob was updated to match. Preference, not a
  bug: the servicetag directory already scopes the file, but having the
  tag in the filename itself matters when a file is copied out of that
  directory. Found because an old cache file predating even the original
  `specs.<ext>` convention (named `<servicetag>.<ext>` already, just
  lowercase before 0.5.1) wasn't being picked up; that file has now been
  renamed on disk to match this convention going forward.

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

## [0.5.3] - `--engine attach` / `--debugger-address` (unconfirmed)

- Added `--engine attach`, which drives a Chrome you launched yourself with
  `--remote-debugging-port` (Selenium `debuggerAddress`) instead of starting
  a fresh automated one, plus `--debugger-address HOST:PORT` (default
  `127.0.0.1:9222`). Motivation: `--servicetag` resolution and `--specs`
  were still blocked by Akamai in headed mode on every other engine, and a
  real, hand-launched profile avoids the fresh-profile/automation-flag
  fingerprints. Never tried before this version (no earlier entry mentions
  attaching to a running browser).
- `dwelf.py` opens its own window in the attached browser and `quit()`
  closes only that window, never the user's browser. The Chrome must use a
  non-default `--user-data-dir` (Chrome 136+ ignores the debugging port on
  the default profile).
- **Unconfirmed:** not yet tested against Dell's real site. CDP is still in
  use, so some tells may remain.
- `--list categories`/`os` now prints a one-line `Error:` and exits 1 when
  the browser can't be built (previously a raw traceback), which `--engine
  attach` hits whenever no Chrome is listening on `--debugger-address`.
  Verified: with nothing listening, the error names the address and the
  launch command. The attach itself has not been tested against a running
  Chrome.

## [0.5.4] - `--engine attach` tested: still blocked for `--servicetag`

- Ran `python3 dwelf.py --servicetag C2PZXZ3 --specs --engine attach` (user
  run, attached to a hand-launched Chrome). Result: the same `Could not
  resolve service tag ... after 3 attempts` failure the other engines give.
  So a real, hand-launched Chrome over `--remote-debugging-port` does **not**
  reliably get past Akamai's service-tag lookup block.
- Limits of this result: one run, one tag, three attempts. Not recorded
  whether the profile was fresh or long-used, or whether any attempt showed
  the checkbox challenge. Treat as "no evidence it helps", not proof it
  never can.
- `--engine attach` is kept (it works and closes only its own window), but
  the README no longer presents it as a likely fix.

## [0.5.5] - Tried Tencent BrowserSkill (`bsk` 0.3.2) for `--servicetag`

- Manual test, no `dwelf.py` code involved: drove the user's own logged-in
  Chrome through `bsk` (navigate to the PowerEdge R630 overview, `fill`
  `#homemfe-dropdown-input` with `6JW6H73`, `click` `#btnSubmit_dep`).
- Result: Akamai's "I'm not a robot" checkbox challenge (`sec-cpt-if`)
  appeared on the first lookup, and the tag did not resolve for 24 s. So
  BrowserSkill does **not** avoid the challenge. Same behaviour as the
  other engines.
- After the user ticked the checkbox and pressed Proceed by hand, Dell
  resolved `6JW6H73` to an OptiPlex 7080 Micro (a "You are changing to"
  confirmation with the tag and an Express Service Code). One run, one tag.
- Not tested: whether `bsk click` on the checkbox would pass, and whether a
  later lookup in the same real profile gets the challenge less often.
  No `bsk` engine added.

## [0.5.6] - `bsk` repeat lookup: no challenge this time (checkbox click untested)

- Repeated the 0.5.5 manual `bsk` test (new session, same tag `6JW6H73`)
  shortly after the user had solved the checkbox by hand in that profile.
  This time the tag resolved straight away to the OptiPlex 7080 Micro
  "Change product" confirmation, with **no** Akamai challenge shown.
- So whether a scripted `bsk click` on the checkbox passes is still
  untested: no challenge appeared to click. A plausible, unproven reading
  is that the earlier human solve left the profile trusted for a while.
- Both runs used the user's own logged-in Chrome. No `dwelf.py` code change.

## [0.5.7] - `bsk` in a clean profile: scripted checkbox click passed

- Clean Chrome profile (`dwelf-test`, no sign-in, BrowserSkill extension
  only), driven with `bsk`, tag `6JW6H73`, no human interaction with the
  challenge. First submit: spinner for ~60 s, no result and no visible
  challenge (the silent block). Second submit (page reloaded and tag
  re-entered): Akamai's challenge iframes (`sec-text-if`, `sec-cpt-if`) appeared.
- `bsk snapshot` listed the checkbox (`@e1`, "I'm not a robot") and
  Proceed (`@e2`) inside the iframe; plain CSS selectors did not match
  through the iframe, but `bsk click @e1` then `bsk click @e2` did. The
  challenge cleared and the tag resolved to the OptiPlex 7080 Micro
  "Change product" confirmation.
- So a scripted click through BrowserSkill passes the checkbox in a clean
  real profile. Limits: one run, one tag; the checkbox still read
  `[unchecked]` in the snapshot after the click, so it is the Proceed click
  that visibly cleared it; first-attempt silent block still happened.
- No `bsk` engine added yet; this only shows it is viable.

## [0.5.8] - Direct `servicetag/<tag>` URLs skip the lookup widget (via `bsk`)

- Never tried before: Dell's service-tag URL form. Loading
  `https://www.dell.com/support/home/en-au/product-support/servicetag/6JW6H73/overview`
  in a real Chrome (driven by `bsk`, `dwelf-test` profile) redirected to
  `.../support/product-details/en-au/servicetag/6JW6H73/overview` and
  rendered "Support for OptiPlex 7080 Micro" directly: no lookup widget, no
  silent first-submit failure, no Akamai challenge.
- The same form works per page type: `.../servicetag/6JW6H73/drivers` loaded
  "Drivers & Downloads" with result rows present. So `--servicetag` may not
  need to resolve a `/product/<slug>` at all.
- The page did not expose a `/product/<slug>` link, so the slug itself is
  not recoverable from it this way.
- Plain HTTP is still blocked: `curl` to the same URL returns `403`. A real
  browser is still required.
- Limits: one tag, tested in a profile that had already solved a challenge
  earlier the same day, so it may be benefiting from trust. Not yet tested
  in a fresh profile or from `dwelf.py`'s own engines. No code change yet.

## [0.5.9] - Direct `servicetag/<tag>` URL confirmed with `dwelf.py`'s own engines

- Tested in fresh automated browsers (no `bsk`, no prior human solve),
  tag `6JW6H73`: `--engine uc` and `--engine selenium` both loaded
  `.../en-au/servicetag/6JW6H73/overview` as "Support for OptiPlex 7080
  Micro" with no Akamai challenge and no lookup widget.
- End to end with no code change: `python3 dwelf.py --url
  "https://www.dell.com/support/product-details/en-au/servicetag/6JW6H73/drivers"
  --engine uc --no-cache --category BIOS` scraped the real result (Dell
  OptiPlex 7080 System BIOS, Critical, `dl.dell.com` link). The existing
  row scraping and filters work unchanged on this URL form.
- Not tested: `--engine firefox`, other tags/product lines, other `--type`
  values, `--specs`, or repeated runs (one run per engine).
- Found along the way: `find_chrome_binary()` does not look in macOS
  locations, so on macOS `--chrome-binary "/Applications/Google
  Chrome.app/Contents/MacOS/Google Chrome"` was needed for `uc`/`selenium`.
  Not fixed here.

## [0.6.0] - `--specs` flow confirmed on the direct `servicetag/<tag>` URL; found a crash in `run_specs()`

- First live confirmation of the `--specs` export flow: with the service-tag
  lookup replaced by loading
  `https://www.dell.com/support/product-details/en-au/servicetag/6JW6H73/overview`
  (throwaway script reusing `run_specs()`'s own helpers and selectors, `--engine uc`,
  fresh automated browser), `#review-specs-drawer-trigger` was found and
  clicked, `#review-specs-drawer` reported `aria-hidden="false"`, the
  `Export` link was clicked, and `6JW6H73.csv` (125 data rows: Component,
  Part Number, Description, Quantity) was downloaded. No Akamai challenge
  at any point.
- This also confirms the drawer's open state *is* signalled by
  `aria-hidden` flipping to `"false"`, which `run_specs()`'s comment had
  only inferred.
- **Bug found, not yet fixed:** `run_specs()` (`dwelf.py`, the
  `WebDriverWait(...).until(EC.attribute_to_be(...))` call) uses
  `EC.attribute_to_be`, which does not exist in Selenium (4.49.0 here has
  only `element_attribute_to_include` and
  `text_to_be_present_in_element_attribute`). It raises `AttributeError`,
  which the surrounding `except TimeoutException` does not catch, so
  `--specs` crashes at that step whenever it is reached. The test used an
  equivalent lambda condition instead.
- Limits: one tag, `uc` only; `run_specs()` itself was not modified, so
  `--specs --servicetag` still uses the widget path and has the crash above.

## [0.6.1] - Fixed `--specs` crash on a non-existent Selenium condition

- `run_specs()` waited for the Product Specifications drawer with
  `EC.attribute_to_be`, which does not exist in Selenium, so `--specs`
  raised `AttributeError` at that step. It now waits with a lambda checking
  `#review-specs-drawer`'s `aria-hidden == "false"`, the condition confirmed
  working live in 0.6.0.
- Verified only by `py_compile` here; the equivalent lambda was exercised
  live in 0.6.0.

## [0.6.2] - `find_chrome_binary()` finds Chrome on macOS

- On macOS, `--engine uc`/`selenium` failed with "Could not find a Chrome
  or Chromium binary" unless `--chrome-binary` was given, because Chrome is
  not on `PATH`. `find_chrome_binary()` now also checks
  `/Applications/Google Chrome.app/...` and `/Applications/Chromium.app/...`.
- Verified by running `find_chrome_binary()` on the macOS machine used for
  testing.

## [0.6.3] - `--servicetag` and `--specs` use the direct `servicetag/<tag>` URL

- `run_scrape()` (`--servicetag` with any `--type`) and `run_specs()` now
  first load `https://www.dell.com/support/product-details/{locale}/servicetag/{tag}/<page>`
  (new `build_service_tag_url()` / `open_service_tag_page()`) instead of
  typing the tag into the overview page's lookup widget. If the browser
  does not stay on that tag's URL (or lands on an "Access Denied" page) it
  falls back to the old `resolve_service_tag_slug()` path unchanged.
- Confirmed live through the real CLI, `--engine uc`, fresh automated
  browser, tag `6JW6H73`, no Akamai challenge and no fallback triggered:
  `--type drivers --category BIOS` (1 result, the OptiPlex 7080 System
  BIOS), `--type manuals` (OptiPlex 7080 Micro manuals), and `--specs`
  (saved `6JW6H73.csv`).
- Not tested: `--engine selenium`/`firefox` through the CLI, other tags or
  product lines, the remaining `--type` values (`articles`, `videos`,
  `advisories`, `regulatory`; the URL is built the same way), or the
  fallback branch (never triggered). The cache is still keyed on the
  `--servicetag` label as before.

## [0.6.4] - Wider testing of the direct `servicetag/<tag>` URL: works, then Akamai starts denying it

- Through the CLI, `--servicetag 6JW6H73` on the direct URL, `--engine uc`:
  `--type regulatory` returned 7 documents, `--type videos` 18, and
  `--type articles` / `--type advisories` returned 0 (articles also 0 on the
  old `/product/optiplex-7080-micro/` URL, so that is Dell's data, not the
  new URL). `--type videos --engine selenium` also returned 18. `--type
  drivers`/`manuals`/`--specs` were confirmed in 0.6.3.
- `--engine uc` intermittently crashes with `from unknown error: web view
  not found`: seen on service-tag videos (2 of 3 runs) and on the old
  slug URL for advisories (1 run), so it is not caused by the new URL.
  Cause not investigated. Re-running usually works.
- **Not reliable:** later in the same session, `--servicetag C2PZXZ3 --type
  drivers --engine selenium` fell back to the widget (the direct URL
  returned Akamai's `Access Denied`, "Reference #18") and then failed
  resolving through the widget as before. A probe showed `Access Denied` on
  the direct URL for `C2PZXZ3` with both `selenium` and `uc`, and then for
  `6JW6H73` too (which had worked an hour earlier). The old
  `/product/optiplex-7080-micro/resources/manuals` URL still loaded 8
  manuals from the same machine at the same time.
- Reading: after roughly 20 automated loads in about an hour, Akamai began
  denying the `servicetag/...` path to this IP/session type while leaving
  the `/product/<slug>/` pages alone. Whether it is rate-based, temporary,
  or specific to that path is **unknown**; no retry/backoff was tried. So
  the direct URL is a likely fast path, not a guaranteed fix.
- The widget fallback was exercised and behaves as before: a bad tag
  (`ZZZZZZ9`) and the denied `C2PZXZ3` both fell back and failed after 3
  attempts with the existing error message.
- Not testable here: `--engine firefox` (only Firefox Nightly is installed,
  no `geckodriver`).
- No code change.

## [0.6.5] - 2026-10-12

- Retried the direct `servicetag/<tag>` URL with a new tag, `5JD9MP2`
  (Dell PowerEdge R430/R530/T430 family): `python3 dwelf.py --servicetag
  5JD9MP2 --type drivers --engine uc --no-cache --debug` loaded the direct
  URL with no `Access Denied`, no Akamai challenge and no widget fallback,
  and scraped 1 result for the default `BIOS` category (Dell Server BIOS
  PowerEdge R430/R530/T430 Version 2.19.0, Urgent, `dl.dell.com` link).
- So the direct URL works again after the 0.6.4 denial of `6JW6H73` and
  `C2PZXZ3`; that denial was therefore not permanent for this IP. Whether
  it was rate-based or time-limited is still unknown.
- Not tested: other `--type` values, `--specs`, `--engine selenium`/`firefox`
  for this tag, repeated runs.
- No code change; version bump only.

## [0.6.6] - 2026-10-12

- `--specs` confirmed live on a second tag, `5JD9MP2` (PowerEdge T430):
  `python3 dwelf.py --servicetag 5JD9MP2 --specs --engine uc --no-cache
  --debug` loaded the direct `servicetag/<tag>` URL, drove the Product
  Specifications drawer, downloaded `5JD9MP2.csv` (88 lines, columns
  `Component,Part Number,Description,Quantity`) into
  `~/.dwelf/cache/5JD9MP2/` and rendered it as a table. No Akamai denial or
  widget fallback.
- Observed: the CSV was saved to the cache directory even with
  `--no-cache` (the download directory is the cache directory); not
  investigated.
- Not tested: `--engine selenium`/`firefox` for `--specs`, other product
  lines.
- No code change; version bump only.
