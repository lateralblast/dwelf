#!/usr/bin/env python3
"""
Scrape Dell's support "Drivers & Downloads" page for a product, filtered
by a driver Category (default: BIOS).

Default target:
    https://www.dell.com/support/home/en-au/product-support/product/poweredge-r630/drivers

Why Selenium instead of `requests`:
  - The page's driver list is rendered client-side (React), so a plain HTML
    fetch never contains the results, only the app shell.
  - Dell fronts the site with Akamai bot management, which returns a hard
    403 "Access Denied" to typical scripted requests regardless of headers.
    Driving a real Chrome browser (with the usual automation fingerprints,
    e.g. navigator.webdriver, suppressed) is enough to get past this in
    most environments - EXCEPT headless mode, which Akamai reliably blocks
    outright (confirmed with both plain Selenium and undetected-chromedriver
    - see --engine below). So this script runs non-headless by default.
  - --servicetag's lookup is protected separately and more aggressively:
    even non-headless, most automated attempts get silently blocked with
    no visible error, and occasionally an interactive "I'm not a robot"
    checkbox challenge appears instead (which this script attempts to
    solve automatically). See SERVICE_TAG_INPUT_ID's comment for what was
    confirmed by testing.
  - --engine firefox (see below) got through on a URL that was blocking
    Chrome (both other engines) outright in the same environment,
    confirmed by testing a full driver scrape end-to-end. This is likely
    because Akamai's bot-detection models are tuned mostly against
    Chrome-based automation. It did NOT meaningfully improve --servicetag
    specifically, though - confirmed by testing that its lookup still gets
    silently blocked most of the time via Firefox too, suggesting that one
    endpoint has its own stricter (and less browser-fingerprint-dependent)
    protection.

Requirements:
    pip install selenium
    Google Chrome or Chromium installed (Selenium's built-in "Selenium
    Manager" downloads a matching chromedriver automatically; you do not
    need to install chromedriver yourself). On Debian/Ubuntu:
        sudo apt install chromium-browser   # or: google-chrome-stable

    For --engine firefox: a NON-SNAP Firefox + geckodriver. Confirmed by
    testing that Ubuntu's default snap-packaged Firefox cannot be
    automated at all (its sandboxing blocks Selenium/geckodriver from
    accessing the profile directory they create). Selenium Manager doesn't
    reliably help here either, since a snap `geckodriver` wrapper on PATH
    gets picked up ahead of it. A standalone build sidesteps all of this:
        curl -sL -o /tmp/firefox.tar.xz 'https://download.mozilla.org/?product=firefox-latest&os=linux64&lang=en-US'
        tar xf /tmp/firefox.tar.xz -C /tmp
        curl -sL -o /tmp/geckodriver.tar.gz https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-linux64.tar.gz
        tar xf /tmp/geckodriver.tar.gz -C /tmp && chmod +x /tmp/geckodriver
    find_firefox_binary()/find_geckodriver_binary() auto-detect a
    non-snap install if one is already on PATH; --firefox-binary /
    --geckodriver-binary override auto-detection otherwise.

Running unattended on a server/CI box with no display:
    Non-headless Chrome needs a real (or virtual) X display, and --headless
    gets blocked by Dell's site (see above), so use Xvfb to give Chrome a
    virtual display instead of an actual monitor:
        sudo apt install xvfb
        xvfb-run -a python3 dwelf.py ...
    The script detects a missing DISPLAY on Linux and raises a clear error
    pointing here rather than letting Chrome crash unhelpfully.
    CONFIRMED WORKING: this got past Dell's bot protection and returned
    correct results even from a network that headless Chrome (both engines)
    and plain curl were blocked from - Xvfb is a fully real, non-headless
    Chrome render target, just an off-screen one, so none of the headless
    detection above applies to it.

Usage (runs with a visible Chrome window by default - see --headless below):
    One of --model, --url, or --servicetag is required - running with none
    of them prints usage and exits rather than assuming a product.

    python3 dwelf.py --model R630              # type=drivers, Category=BIOS, OS=BIOS
    python3 dwelf.py --model R730              # same, for the R730 instead
    python3 dwelf.py --model "Dell Precision Tower 3420"   # non-PowerEdge line, its own slug rule
    python3 dwelf.py --model "Dell Precision Compact 3260"   # same line, different form factor -> different prefix
    python3 dwelf.py --model "Dell Optiplex 3000 Micro"   # another line, no prefix/suffix at all
    python3 dwelf.py --model "OptiPlex 3040 Small Form Factor"   # same line, abbreviated form factor
    python3 dwelf.py --model "Latitude 3460"   # laptop line, always gets a "-laptop" suffix
    python3 dwelf.py --model "XPS 13 9340"    # two numbers -> laptop; one number (e.g. "XPS 8940") -> desktop
    python3 dwelf.py --model "Inspiron 24 5410 All-in-One"   # same token-count rule as XPS, but a word can override it
    python3 dwelf.py --model R630 --type manuals            # Manuals & Documents instead of drivers
    python3 dwelf.py --model R630 --type articles           # KB Articles (capped at 30 for a signed-out session)
    python3 dwelf.py --model R630 --type videos             # Videos (full list, no cap)
    python3 dwelf.py --model R630 --type advisories         # Security advisories (Technical tab not fetched)
    python3 dwelf.py --model R630 --type advisories --impact High   # only High-impact advisories
    python3 dwelf.py --model R630 --type regulatory         # Regulatory compliance documents
    python3 dwelf.py --model R630 --type manuals --search "release notes"   # only results containing this text
    python3 dwelf.py --servicetag 1MJ4LG2      # resolve a tag instead of guessing --model (intermittent, see below)
    python3 dwelf.py --model R630 --category Firmware --os "Windows Server 2019 LTSC"
    python3 dwelf.py --model R630 --os none    # leave Dell's default OS selection alone
    python3 dwelf.py --url <a product's drivers URL> --category BIOS  # instead of --model/--type
    python3 dwelf.py --geturl --model r630 --type manuals   # just print the constructed URL and exit
    python3 dwelf.py --debug                  # dump screenshots/HTML at each step
    python3 dwelf.py --headless               # blocked by Dell's bot protection; kept for completeness
    python3 dwelf.py --engine uc               # undetected-chromedriver backend instead of plain Selenium
    python3 dwelf.py --engine firefox          # Firefox instead of Chrome - confirmed more reliable (see above)
    python3 dwelf.py --output drivers.csv
    python3 dwelf.py --model R630 --download           # also fetch each file into $HOME/firmware/r630
    python3 dwelf.py --model R630 --download --directory /path/to/dir   # ...or a specific directory
    python3 dwelf.py --chrome-binary /path/to/chrome   # if auto-detect fails
    python3 dwelf.py --engine firefox --firefox-binary /path/to/firefox --geckodriver-binary /path/to/geckodriver
    xvfb-run -a python3 dwelf.py              # unattended, no display available (confirmed working)
"""

import argparse
import csv
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from typing import List, Optional

__version__ = "0.4.0"
__long_name__ = "Dell Website Equipment Link Finder"


def ensure_package(import_name: str, pip_name: Optional[str] = None) -> None:
    """Import `import_name`, installing it with pip first if it's missing."""
    try:
        importlib.import_module(import_name)
        return
    except ImportError:
        pass

    pip_name = pip_name or import_name
    print(f"[setup] '{import_name}' not found; installing with pip ({pip_name})...", file=sys.stderr)
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--user", pip_name], check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to auto-install '{pip_name}' with pip: {e}") from e

    importlib.import_module(import_name)  # re-raises ImportError if still missing


ensure_package("selenium")

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

CHROME_BINARY_CANDIDATES = [
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "chrome",
]

FIREFOX_BINARY_CANDIDATES = ["firefox", "firefox-esr", "firefox-developer-edition"]
GECKODRIVER_CANDIDATES = ["geckodriver"]

DEFAULT_TYPE = "drivers"
DEFAULT_LOCALE = "en-au"

# All of these live under "support/product-details". "drivers" originally
# used a different template ("support/home/{locale}/product-support/product/
# {slug}/drivers"), which still works but is just a legacy entry point:
# confirmed by testing (Firefox) that navigating there redirects straight to
# this same "product-details" URL - which also confirmed to load correctly
# when used directly, for both PowerEdge (poweredge-r630) and non-PowerEdge
# (precision-t3420-workstation) slugs. Each entry is a template taking
# {locale} and {slug}.
TYPE_URL_TEMPLATES = {
    "drivers": "https://www.dell.com/support/product-details/{locale}/product/{slug}/drivers",
    "manuals": "https://www.dell.com/support/product-details/{locale}/product/{slug}/resources/manuals",
    "articles": "https://www.dell.com/support/product-details/{locale}/product/{slug}/resources/articles",
    "videos": "https://www.dell.com/support/product-details/{locale}/product/{slug}/resources/videos",
    "advisories": "https://www.dell.com/support/product-details/{locale}/product/{slug}/resources/advisories",
    "regulatory": "https://www.dell.com/support/product-details/{locale}/product/{slug}/resources/regulatory",
}

# Alternate names for a type in TYPE_URL_TEMPLATES, e.g. --type documents
# is just another name for --type manuals (same URL, same scraping).
TYPE_ALIASES = {"documents": "manuals", "downloads": "drivers"}

# Types this script knows how to extract results from. "drivers" and
# "advisories" have Category/OS/Impact filter widgets and a DDS grid
# respectively (advisories only returns the default "Security" tab - see
# ADVISORY_ROW_SELECTOR's comment); "manuals", "articles", "videos" and
# "regulatory" are plain lists/grids with no filtering (articles is capped
# at 30 rows for a signed-out session - see ARTICLE_ROW_SELECTOR's comment;
# videos has no such cap - see VIDEO_ROW_SELECTOR's comment). Any other
# configured type just navigates and dumps debug artifacts so support can
# be added once its markup is known.
SCRAPABLE_TYPES = {"drivers", "manuals", "articles", "videos", "advisories", "regulatory"}


def normalize_type(type_: str) -> str:
    key = type_.strip().lower()
    return TYPE_ALIASES.get(key, key)


# Dell Precision desktop form factors don't share one abbreviation rule:
# each maps to its own (possibly empty) prefix on the model number, e.g.
# "Dell Precision Tower 3420" -> "precision-t3420-workstation" but
# "Dell Precision Compact 3260" -> "precision-3260-workstation" (no letter
# at all) - both confirmed by testing the resulting URL against the real
# site. Unrecognized form-factor words fall through to the generic rule
# below rather than guessing a prefix.
PRECISION_FORM_FACTOR_PREFIXES = {
    "tower": "t",
    "compact": "",
}

# Product lines whose slug is just lowercase-hyphenate of the model name,
# with no "poweredge-"-style prefix assumed - e.g. "Dell Optiplex 3000
# Micro" -> "optiplex-3000-micro" (confirmed by testing the resulting URL
# against the real site). The others here aren't individually confirmed the
# same way, but assuming no prefix for a model that already names its own
# product line is still strictly safer than force-prepending "poweredge-"
# to it, which is definitely wrong.
KNOWN_PRODUCT_LINES = {"poweredge", "precision", "optiplex", "latitude", "xps", "inspiron", "vostro", "alienware"}

# Unlike Precision (form factor before the model number), OptiPlex puts the
# number first and a full form-factor description after it, which Dell
# abbreviates in the slug, e.g. "OptiPlex 3040 Small Form Factor" ->
# "optiplex-3040-sff" - confirmed by testing the resulting URL against the
# real site. An unrecognized form-factor description (like plain "Micro",
# which needs no abbreviation - see KNOWN_PRODUCT_LINES's example) falls
# through to the generic rule rather than guessing one.
OPTIPLEX_FORM_FACTOR_ABBREVIATIONS = {"small form factor": "sff"}

# Inspiron follows the same token-count fallback as XPS (one number ->
# desktop, two -> laptop) EXCEPT an explicit trailing form-factor word
# overrides it - notably "All-in-One" gives "-aio", not "-laptop", even
# though it has two numbers before it ("24 5410 All-in-One") - all
# confirmed by testing the resulting URL against the real site for one
# example of each: bare one-number ("3650"), one-number with an explicit
# "Desktop" word ("3020 Desktop"), bare two-number ("15 3530"), and
# two-number with "All-in-One".
INSPIRON_TRAILING_FORM_FACTORS = {"desktop": "desktop", "all-in-one": "aio", "aio": "aio"}


def normalize_model_slug(model: str) -> str:
    """Turn a descriptive model name into a Dell product slug.

    Dell's slugs aren't a uniform transform of the model name across
    product lines, so this handles known special cases first, falling
    back to the original PowerEdge-assuming rule this script started with:

    - Dell Precision <form factor> <N> -> "precision-<prefix><n>-workstation"
      for a form factor in PRECISION_FORM_FACTOR_PREFIXES (currently Tower
      and Compact - see its comment for confirmed examples).
    - OptiPlex <N> <form factor description> ->
      "optiplex-<n>-<abbreviation>" for a description in
      OPTIPLEX_FORM_FACTOR_ABBREVIATIONS (currently just Small Form Factor
      - see its comment).
    - Latitude <N> (and nothing else) -> "latitude-<n>-laptop", e.g.
      "Latitude 3460" -> "latitude-3460-laptop" (confirmed by testing the
      resulting URL against the real site).
    - XPS <N> <N> -> "xps-<n>-<n>-laptop" (two numbers, e.g. "XPS 13 9340")
      vs XPS <N> -> "xps-<n>-desktop" (one number, e.g. "XPS 8940") - the
      token count is the only distinguishing signal, confirmed by testing
      the resulting URL against the real site for two examples of each.
    - Inspiron follows the same token-count fallback as XPS, but an
      explicit trailing form-factor word overrides it - see
      INSPIRON_TRAILING_FORM_FACTORS's comment for confirmed examples,
      notably "All-in-One" giving "-aio" even with two numbers.
    - Anything else: lowercase + hyphenate, e.g. "Optiplex 3000 Micro" ->
      "optiplex-3000-micro". "poweredge-" is only prepended if the result
      doesn't already start with a name in KNOWN_PRODUCT_LINES, e.g. a bare
      "R730" -> "poweredge-r730" (what this script has mainly been used
      against) but "Optiplex ..." is left alone. An unrecognized product
      line not in that set will still incorrectly get "poweredge-"
      prepended - pass a full correct slug directly, or use --url/--geturl
      to check first.
    """
    cleaned = re.sub(r"^\s*dell\s+", "", model.strip(), flags=re.IGNORECASE)

    precision = re.match(r"precision\s+(\w+)\s+(\w+)", cleaned, re.IGNORECASE)
    if precision:
        form_factor, number = precision.group(1).lower(), precision.group(2).lower()
        if form_factor in PRECISION_FORM_FACTOR_PREFIXES:
            prefix = PRECISION_FORM_FACTOR_PREFIXES[form_factor]
            return f"precision-{prefix}{number}-workstation"

    optiplex = re.match(r"optiplex\s+(\w+)\s+(.+)", cleaned, re.IGNORECASE)
    if optiplex:
        number, form_factor_desc = optiplex.group(1).lower(), optiplex.group(2).strip().lower()
        if form_factor_desc in OPTIPLEX_FORM_FACTOR_ABBREVIATIONS:
            abbreviation = OPTIPLEX_FORM_FACTOR_ABBREVIATIONS[form_factor_desc]
            return f"optiplex-{number}-{abbreviation}"

    # Unlike Precision/OptiPlex, Latitude is laptop-only, so there's no
    # form factor to look up - "-laptop" is appended unconditionally, but
    # only for a bare "Latitude <model>" (anchored to end of string) since
    # that's the only form confirmed by testing the resulting URL against
    # the real site; anything with extra words falls through to the
    # generic rule below rather than guessing "-laptop" is still right.
    latitude = re.match(r"latitude\s+(\w+)\s*$", cleaned, re.IGNORECASE)
    if latitude:
        return f"latitude-{latitude.group(1).lower()}-laptop"

    # XPS spans both laptops and desktop towers with no word distinguishing
    # them in the model name (unlike OptiPlex/Precision) - only the number
    # of tokens does: two ("13 9340") is a laptop, one ("8940") is a
    # desktop tower - confirmed by testing the resulting URL against the
    # real site for two examples of each. Anything else (e.g. a "2-in-1"
    # variant, unconfirmed) falls through to the generic rule.
    xps = re.match(r"xps\s+(.+)", cleaned, re.IGNORECASE)
    if xps:
        rest_tokens = xps.group(1).strip().split()
        if len(rest_tokens) == 1:
            return f"xps-{rest_tokens[0].lower()}-desktop"
        elif len(rest_tokens) == 2:
            return f"xps-{rest_tokens[0].lower()}-{rest_tokens[1].lower()}-laptop"

    inspiron = re.match(r"inspiron\s+(.+)", cleaned, re.IGNORECASE)
    if inspiron:
        rest = inspiron.group(1).strip()
        for phrase, abbreviation in INSPIRON_TRAILING_FORM_FACTORS.items():
            suffix_match = re.match(rf"^(.*?)\s+{re.escape(phrase)}$", rest, re.IGNORECASE)
            if suffix_match:
                numbers_slug = re.sub(r"\s+", "-", suffix_match.group(1).strip().lower())
                return f"inspiron-{numbers_slug}-{abbreviation}"
        rest_tokens = rest.split()
        if len(rest_tokens) == 1:
            return f"inspiron-{rest_tokens[0].lower()}-desktop"
        elif len(rest_tokens) == 2:
            return f"inspiron-{rest_tokens[0].lower()}-{rest_tokens[1].lower()}-laptop"

    slug = re.sub(r"[\s/\\-]+", "-", cleaned.lower()).strip("-")
    if slug.split("-", 1)[0] not in KNOWN_PRODUCT_LINES:
        slug = f"poweredge-{slug}"
    return slug


def build_product_url(model: str, type_: str = DEFAULT_TYPE, locale: str = DEFAULT_LOCALE) -> str:
    """Turn a model name into a Dell product-support URL - see
    normalize_model_slug() for how the model is turned into a slug.

    `type_` selects which URL template (and therefore which product-support
    page) to build, e.g. "drivers" or "manuals" - see TYPE_URL_TEMPLATES.
    """
    slug = normalize_model_slug(model)

    type_key = normalize_type(type_)
    try:
        template = TYPE_URL_TEMPLATES[type_key]
    except KeyError:
        known = sorted(set(TYPE_URL_TEMPLATES) | set(TYPE_ALIASES))
        raise ValueError(
            f"Unknown --type '{type_}'. Known types: {', '.join(known)}. "
            "Use --url directly for anything else."
        )
    return template.format(slug=slug, locale=locale)

# Selectors below target Dell's own "DDS" (Dell Design System) component
# markup, confirmed by inspecting a live render of the R630 drivers page:
#   - Category filter is a multi-select combobox: an <input id="dnd-cat-
#     dropdown-control"> trigger that reveals a listbox (#dnd-cat-dropdown-
#     popup) of <button class="dds__dropdown__item-option"> options, each
#     labeled e.g. "BIOS (1)" (name + a live count for the current filters).
#   - Operating system is a single-select combobox with the same option
#     markup, trigger <input id="dnd-os-dropdown-control">, options inside
#     <ul id="dnd-os-dropdown-popup-list">. Dell exposes "BIOS" as one of
#     its OS choices (an OS-agnostic bucket for BIOS/firmware updates).
#   - Results render as an ARIA grid: row containers are
#     <div class="dds__tr" role="row" data-row="N"> (the header row has no
#     data-row attribute, so [data-row] excludes it), each with gridcells in
#     a fixed order: [checkbox, name, importance, release date, category,
#     action/download].
COOKIE_BUTTON_SELECTORS = [
    (By.ID, "onetrust-accept-btn-handler"),
    (By.XPATH, "//button[contains(translate(., 'ACEPT', 'acept'), 'accept')]"),
]

CATEGORY_TRIGGER_ID = "dnd-cat-dropdown-control"
CATEGORY_POPUP_ID = "dnd-cat-dropdown-popup"
OS_TRIGGER_ID = "dnd-os-dropdown-control"
OS_POPUP_ID = "dnd-os-dropdown-popup-list"

ROW_SELECTOR = "div[id^='table-'] div.dds__tr[data-row]"
GRIDCELL_SELECTOR = "[role='gridcell']"
# Index into a row's gridcells (0 = row-selection checkbox).
COL_NAME, COL_IMPORTANCE, COL_DATE, COL_CATEGORY, COL_ACTION = 1, 2, 3, 4, 5

# The "manuals" page (support/product-details/.../resources/manuals) has a
# much simpler, non-DDS-grid layout: a plain list of entries inside
# #manualsdetails, each a direct <div class="dds__col--lg-12 ..."> child
# with a title link (a.manual-link > h5), a doc-type line (div.dds__body-2),
# and an "Updated: <date>" line (.updated-id).
MANUALS_CONTAINER_ID = "manualsdetails"
MANUAL_ROW_SELECTOR = f"#{MANUALS_CONTAINER_ID} > div.dds__col--lg-12"

# The "articles" page (support/product-details/.../resources/articles) shares
# the manuals page's general layout (same #<container> > div.dds__col--lg-12
# row shape, a.<x>-link title, div.dds__body-2 blurb), but each row also has
# a real KB article ID alongside the "Updated:" date. Dell caps the public
# (signed-out) view at 30 of however many total articles exist - the "Show
# More" button (#articles-loadmore) doesn't add rows for an anonymous
# session (confirmed by testing: click succeeds, row count doesn't change),
# so this script returns that same first batch rather than pretending to
# paginate through content that needs a Dell account to unlock.
ARTICLES_CONTAINER_ID = "articlesisgdetails"
ARTICLE_ROW_SELECTOR = f"#{ARTICLES_CONTAINER_ID} > div.dds__col--lg-12"

# The "videos" page (support/product-details/.../resources/videos) is a card
# grid rather than a list: #videodetails contains a div.dds__row of
# div.dds__col--lg-3 cards. Unlike articles, ALL of them (confirmed: 75/75
# for the R630) are already present in the DOM on load - the "Show More"
# button (#videos-loadmore) just toggles visibility (CSS) on cards already
# there rather than fetching more, so find_elements() alone returns the
# complete list with no pagination workaround needed. Each card has two
# a.video-card-link anchors sharing the same href (a thumbnail-only one with
# no text, and a titled one - distinguished here by which has .text), plus
# two div.dds__body-3 siblings in DOM order: [date, duration].
VIDEOS_CONTAINER_ID = "videodetails"
VIDEO_ROW_SELECTOR = f"#{VIDEOS_CONTAINER_ID} div.dds__col--lg-3"

# The "advisories" page (support/product-details/.../resources/advisories)
# is back to a DDS grid like the drivers page, but with role="cell" (not
# "gridcell") and a "Security"/"Technical" tab pair, only the active
# "Security" tab (#table-adv-product) is populated on load - "Technical"
# (#table-adv-product-eta) stays an empty <div> until that tab is clicked,
# so only Security advisories are returned. Each data row is immediately
# followed by a same-data-row "dds__tr__expandable" detail row (collapsed,
# empty unless expanded), which :not(.dds__tr__expandable) excludes. Column
# order: [expand button, impact, advisory ID + link, title, last updated].
ADVISORY_TABLE_ID = "table-adv-product"
ADVISORY_ROW_SELECTOR = f"#{ADVISORY_TABLE_ID} div.dds__tr[data-row]:not(.dds__tr__expandable)"
ADVISORY_CELL_SELECTOR = "[role='cell']"
ADV_COL_IMPACT, ADV_COL_ID, ADV_COL_TITLE, ADV_COL_UPDATED = 1, 2, 3, 4

# The Impact filter is the same DDS multi-select combobox as Category/OS,
# but its trigger/popup ids include a randomly-generated numeric suffix
# that differs per page load (e.g. "Dropdown-control-663422481"), so unlike
# CATEGORY_TRIGGER_ID/OS_TRIGGER_ID it can't be hardcoded - it's resolved at
# runtime via the <label for="..."> that says "Impact" (see select_impact).
# Selecting an Impact value also doesn't filter live like Category/OS do;
# it requires clicking the separate "Apply" button below the filter row.
ADVISORY_APPLY_BUTTON_ID = "esaFilterSubmitBtn"

# The "regulatory" page (support/product-details/.../resources/regulatory)
# shares the manuals/articles list layout, but nested one level deeper
# (rows live under #rdocdetail's #tabs-rdoc > div.dds__row, like videos).
# A sibling "N out of N shown" counter div also matches div.dds__col--lg-12
# but lacks the .dds__mb-2 class real entries have, so .dds__mb-2 excludes
# it (confirmed by testing: without it, find_regulatory_rows() over-counts
# by one, though scrape_regulatory() already skips the counter safely via
# its missing link). The metadata line has no fixed shape: an unlabelled
# product-name span followed by "Regulatory Model:"/"Regulatory Type:"
# labelled spans, parsed by label prefix rather than position.
REGULATORY_CONTAINER_ID = "rdocdetail"
REGULATORY_ROW_SELECTOR = f"#{REGULATORY_CONTAINER_ID} div.dds__col--lg-12.dds__mb-2"

# --servicetag resolves a service tag to a product slug using a product
# overview page's own "Identify a product" widget, then builds the normal
# --type URL from the resolved slug - i.e. it's an alternative to --model
# that asks Dell which product a real tag belongs to. Any overview page
# works as the entry point (SERVICE_TAG_BASE_SLUG is arbitrary): enter a
# tag and click Submit, and Dell's widget either resolves it directly (if
# it's the same product as the current page) or shows a "change product?"
# confirmation to click through (if it belongs to a different one) -
# confirmed by a user manually testing this flow, which is more direct
# than the support home page's version of the same widget (a real Submit
# button here, vs relying on an Enter keypress there).
#
# This is INTERMITTENT and not yet confirmed to fully succeed end-to-end
# via this script: the backend call this widget makes
# (/support/assetdiscovery/.../validate/asset) is the same one protected
# by Akamai on the support home page, confirmed via browser console logs
# to 403 here too. Most automated attempts get a silent block with the
# page stuck on a permanent loading spinner and no visible feedback;
# sometimes an interactive "I'm not a robot" checkbox challenge (a real
# Akamai Bot Manager interstitial, checked for via try_solve_akamai_
# challenge - top-level document and every iframe, no id/title assumed)
# appears instead. Dell's own genuine rejections (bad tag / no access) do
# surface real messages (SERVICE_TAG_ERROR_IDS), which is how a definite
# "no" is told apart from Akamai silently blocking the request. One
# consequence of using a fixed base slug: if a tag happens to belong to
# SERVICE_TAG_BASE_SLUG itself, there's no distinct signal to tell that
# apart from a silent block, so that case isn't specially detected here.
SERVICE_TAG_INPUT_ID = "homemfe-dropdown-input"
SERVICE_TAG_SUBMIT_BUTTON_ID = "btnSubmit_dep"
SERVICE_TAG_BASE_SLUG = "poweredge-r630"
CHANGE_PRODUCT_DIALOG_ID = "changeProductContentDiv"
SERVICE_TAG_ERROR_IDS = ["dep-msg-invalidServiceTag_dep", "dep-msg-accessDenied_dep"]


@dataclass
class DriverInfo:
    name: str
    category: Optional[str] = None
    release_date: Optional[str] = None
    importance: Optional[str] = None
    download_url: Optional[str] = None


@dataclass
class ManualInfo:
    title: str
    url: Optional[str] = None
    doc_type: Optional[str] = None
    updated: Optional[str] = None


@dataclass
class ArticleInfo:
    title: str
    url: Optional[str] = None
    description: Optional[str] = None
    updated: Optional[str] = None
    article_id: Optional[str] = None


@dataclass
class VideoInfo:
    title: str
    url: Optional[str] = None
    date: Optional[str] = None
    duration: Optional[str] = None
    thumbnail_url: Optional[str] = None


@dataclass
class AdvisoryInfo:
    title: str
    advisory_id: Optional[str] = None
    url: Optional[str] = None
    impact: Optional[str] = None
    last_updated: Optional[str] = None


@dataclass
class RegulatoryInfo:
    title: str
    url: Optional[str] = None
    product: Optional[str] = None
    regulatory_model: Optional[str] = None
    regulatory_type: Optional[str] = None


def find_chrome_binary() -> Optional[str]:
    for name in CHROME_BINARY_CANDIDATES:
        path = shutil.which(name)
        if path:
            return path
    return None


def check_display_available(headless: bool) -> None:
    """Non-headless Chrome needs a real (or virtual) X display to render
    into. Dell's Akamai bot protection reliably blocks headless Chrome (with
    both plain Selenium and undetected-chromedriver - confirmed by testing),
    so this script defaults to non-headless, which then fails with an
    unhelpful native Chrome crash on a display-less Linux host (e.g. a
    server/CI box with no monitor). Xvfb fixes that: it runs a virtual X
    server so non-headless Chrome renders normally without an actual
    monitor, without tripping Dell's headless detection.
    """
    if headless or sys.platform != "linux" or os.environ.get("DISPLAY"):
        return
    raise RuntimeError(
        "No DISPLAY found and --headless was not given. Non-headless Chrome needs "
        "an X display, and this script defaults to non-headless because Dell's "
        "bot protection blocks headless Chrome outright.\n"
        "On a server/CI box with no monitor, run under Xvfb instead:\n"
        "    sudo apt install xvfb\n"
        "    xvfb-run -a python3 dwelf.py ...\n"
        "(--headless is available but not recommended - it gets blocked by Dell's site)"
    )


def build_driver(headless: bool = False, chrome_binary: Optional[str] = None) -> webdriver.Chrome:
    check_display_available(headless)
    binary = chrome_binary or find_chrome_binary()
    if not binary:
        raise RuntimeError(
            "Could not find a Chrome or Chromium binary on this machine.\n"
            "Install one, e.g. on Debian/Ubuntu:\n"
            "    sudo apt install chromium-browser\n"
            "or point at an existing install with --chrome-binary /path/to/chrome"
        )

    options = Options()
    options.binary_location = binary
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=en-AU")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Reduce the automation fingerprints Akamai's bot detection checks for.
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )
    driver.set_page_load_timeout(60)
    return driver


def build_driver_uc(headless: bool = False, chrome_binary: Optional[str] = None):
    """Default backend (--engine uc): undetected-chromedriver, which patches
    the chromedriver binary itself (e.g. removes the "cdc_" markers
    Selenium's chromedriver injects) rather than just setting Selenium
    options. Use --engine selenium for plain Selenium/Chrome instead (no
    extra dependency), or --engine firefox, which testing found gets
    through on some URLs that block Chrome outright (see its own comment).
    """
    check_display_available(headless)
    # undetected-chromedriver still does `from distutils.version import
    # LooseVersion`, which Python 3.12+ removed from the stdlib; installing
    # setuptools first restores it via its bundled compatibility shim.
    ensure_package("setuptools")
    ensure_package("undetected_chromedriver", "undetected-chromedriver")
    import undetected_chromedriver as uc

    binary = chrome_binary or find_chrome_binary()
    if not binary:
        raise RuntimeError(
            "Could not find a Chrome or Chromium binary on this machine.\n"
            "Install one, e.g. on Debian/Ubuntu:\n"
            "    sudo apt install chromium-browser\n"
            "or point at an existing install with --chrome-binary /path/to/chrome"
        )

    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=en-AU")

    driver = uc.Chrome(options=options, browser_executable_path=binary, headless=headless, use_subprocess=True)
    driver.set_page_load_timeout(60)
    return driver


def _is_snap_path(path: str) -> bool:
    """True if `path` is (or resolves to, or is a shell wrapper for) a
    snap-confined binary. Needed because Ubuntu's transitional packages use
    a few different indirection styles that a naive realpath() check
    misses (confirmed by testing against real paths on an Ubuntu machine):
    /usr/bin/firefox is a real (non-symlink) shell script that execs
    /snap/bin/firefox, so its realpath is itself; /snap/bin/geckodriver is
    a symlink whose realpath is /usr/bin/snap (the generic snap launcher),
    which doesn't contain "/snap/" as a directory component either.
    """
    if "/snap/" in path:
        return True
    real = os.path.realpath(path)
    if "/snap/" in real or os.path.basename(real) == "snap":
        return True
    try:
        with open(path, "rb") as f:
            head = f.read(4096)
    except OSError:
        return False
    return head[:2] == b"#!" and b"snap" in head.lower()


def find_firefox_binary() -> Optional[str]:
    """Like find_chrome_binary(), but skips any resolved path inside a snap
    (e.g. Ubuntu's default `firefox` package is a snap wrapper) - confirmed
    by testing that snap Firefox cannot be automated at all: its sandboxing
    blocks it from accessing the temporary profile directory Selenium/
    geckodriver create outside the snap's own confined paths, failing with
    "Your Firefox profile cannot be loaded" or "Process unexpectedly closed
    with status 1" regardless of which geckodriver is used.
    """
    for name in FIREFOX_BINARY_CANDIDATES:
        path = shutil.which(name)
        if path and not _is_snap_path(path):
            return path
    return None


def find_geckodriver_binary() -> Optional[str]:
    """Like find_firefox_binary(), but for geckodriver: Ubuntu's Firefox
    snap also puts a confined `geckodriver` wrapper on PATH
    (/snap/bin/geckodriver) that only accepts the snap's own bundled
    Firefox binary, rejecting any other with "binary is not a Firefox
    executable" - confirmed by testing. Skipping it here means Selenium
    Manager auto-downloads a real one instead when nothing else is found.
    """
    for name in GECKODRIVER_CANDIDATES:
        path = shutil.which(name)
        if path and not _is_snap_path(path):
            return path
    return None


def build_driver_firefox(
    headless: bool = False,
    firefox_binary: Optional[str] = None,
    geckodriver_binary: Optional[str] = None,
) -> webdriver.Firefox:
    """Alternative backend using Firefox instead of Chrome. Opt in with
    --engine firefox. Confirmed by testing: Dell's Akamai protection let a
    plain Firefox session straight through on a URL that was blocking
    Chrome (both plain Selenium and undetected-chromedriver) outright in
    the same environment - Akamai's bot-detection models are presumably
    tuned mostly against Chrome-based automation (Selenium/Puppeteer/
    Playwright overwhelmingly target Chrome), so this may be meaningfully
    more reliable, not just an alternative for its own sake.
    """
    check_display_available(headless)
    binary = firefox_binary or find_firefox_binary()
    if not binary:
        raise RuntimeError(
            "Could not find a non-snap Firefox binary on this machine (a snap-installed one, "
            "Ubuntu's default, cannot be automated - see find_firefox_binary's comment).\n"
            "Install a standalone build instead, e.g.:\n"
            "    curl -sL -o /tmp/firefox.tar.xz 'https://download.mozilla.org/?product=firefox-latest&os=linux64&lang=en-US'\n"
            "    tar xf /tmp/firefox.tar.xz -C /tmp\n"
            "then point at it with --firefox-binary /tmp/firefox/firefox"
        )
    driver_path = geckodriver_binary or find_geckodriver_binary()
    if not driver_path:
        raise RuntimeError(
            "Could not find a non-snap geckodriver on this machine.\n"
            "Install one, e.g.:\n"
            "    curl -sL -o /tmp/geckodriver.tar.gz "
            "https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-linux64.tar.gz\n"
            "    tar xf /tmp/geckodriver.tar.gz -C /tmp && chmod +x /tmp/geckodriver\n"
            "then point at it with --geckodriver-binary /tmp/geckodriver"
        )

    options = FirefoxOptions()
    options.binary_location = binary
    if headless:
        options.add_argument("-headless")
    options.set_preference("intl.accept_languages", "en-AU")
    # Reduce the automation fingerprints Akamai's bot detection checks for.
    options.set_preference("dom.webdriver.enabled", False)

    driver = webdriver.Firefox(options=options, service=FirefoxService(executable_path=driver_path))
    driver.set_window_size(1920, 1080)
    driver.set_page_load_timeout(60)
    return driver


def dismiss_cookie_banner(driver, wait: WebDriverWait) -> None:
    for by, selector in COOKIE_BUTTON_SELECTORS:
        try:
            btn = wait.until(EC.element_to_be_clickable((by, selector)))
            btn.click()
            time.sleep(0.5)
            return
        except TimeoutException:
            continue


def select_dropdown_option(
    driver, trigger_id: str, popup_id: str, value: str, timeout: float = 10, close_after: bool = True
) -> bool:
    """Open a Dell DDS combobox (Category, Operating System and Impact all
    share the same markup) and click the option whose label starts with
    `value`, matched case-insensitively. Category labels carry a live
    " (<count>)" suffix, e.g. "BIOS (1)", so a prefix match is used rather
    than equality.

    `close_after` sends Escape to close the popup once the option is
    clicked. Leave this True for Category/OS, which filter live. Pass
    False for a combobox that needs a separate "Apply" button afterwards
    (e.g. Impact) - Escape appears to clear the tentative multi-select
    state rather than just closing the popup, which would otherwise submit
    an empty selection to Apply (confirmed by testing: the filter silently
    had no effect until this was disabled for that case).
    """
    wait = WebDriverWait(driver, timeout)
    try:
        trigger = wait.until(EC.element_to_be_clickable((By.ID, trigger_id)))
    except TimeoutException:
        return False

    trigger.click()

    lower_value = value.lower()
    option_xpath = (
        f"//*[@id='{popup_id}']"
        "//button[contains(@class,'dds__dropdown__item-option')]"
        "[.//span[starts-with("
        "translate(normalize-space(.), "
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), "
        f"'{lower_value}')]]"
    )
    try:
        option = wait.until(EC.element_to_be_clickable((By.XPATH, option_xpath)))
    except TimeoutException:
        close_dropdown(trigger)
        return False

    option.click()
    if close_after:
        # Single-select dropdowns (e.g. Operating System) auto-close on
        # selection, which can make `trigger` briefly not interactable;
        # multi-select ones (e.g. Category) stay open and need an explicit
        # close. Either way this is just cleanup, so failures aren't fatal.
        close_dropdown(trigger)
    time.sleep(2)  # let the filtered grid re-render / the Apply button pick up the selection
    return True


def close_dropdown(trigger) -> None:
    try:
        trigger.send_keys(Keys.ESCAPE)
    except Exception:
        pass


def select_category(driver, category: str, timeout: float = 10) -> bool:
    return select_dropdown_option(driver, CATEGORY_TRIGGER_ID, CATEGORY_POPUP_ID, category, timeout)


def select_os(driver, os_name: str, timeout: float = 10) -> bool:
    return select_dropdown_option(driver, OS_TRIGGER_ID, OS_POPUP_ID, os_name, timeout)


def select_impact(driver, impact: str, timeout: float = 10) -> bool:
    """Select a value in the advisories page's Impact filter and click
    Apply. Unlike Category/OS, the trigger/popup ids are randomly
    generated per page load, so they're resolved here via the <label> that
    reads "Impact" rather than a hardcoded id.
    """
    wait = WebDriverWait(driver, timeout)
    try:
        label = wait.until(EC.presence_of_element_located((By.XPATH, "//label[normalize-space(.)='Impact']")))
        trigger_id = label.get_attribute("for")
        trigger = driver.find_element(By.ID, trigger_id)
        popup_id = trigger.get_attribute("aria-controls")
    except (TimeoutException, NoSuchElementException):
        return False
    if not trigger_id or not popup_id:
        return False

    if not select_dropdown_option(driver, trigger_id, popup_id, impact, timeout, close_after=False):
        return False

    try:
        apply_button = wait.until(EC.element_to_be_clickable((By.ID, ADVISORY_APPLY_BUTTON_ID)))
        apply_button.click()
    except TimeoutException:
        return False
    time.sleep(2)  # let the filtered table re-render
    return True


def try_solve_akamai_challenge(driver) -> bool:
    """Best-effort: if Akamai's "I'm not a robot" interstitial is showing,
    tick the checkbox and click Proceed. Checks the top-level document
    first, then every iframe on the page in turn - Akamai's challenge has
    been observed both inline and inside a same-origin iframe with an id
    that isn't consistent across sessions (confirmed by testing: a
    selector targeting one specific observed id missed a real challenge a
    user hit), so rather than guessing a selector, every iframe is tried.
    Returns True if a challenge was found and clicked through. Always
    leaves the driver back on the top-level document.
    """

    def find_and_click_here() -> bool:
        # Other, unrelated hidden checkboxes exist elsewhere on Dell's pages
        # (confirmed by testing: an earlier version of this crashed trying
        # to click one), so only a visible one counts, and any interaction
        # failure is swallowed rather than propagated.
        checkboxes = [cb for cb in driver.find_elements(By.XPATH, "//input[@type='checkbox']") if cb.is_displayed()]
        if not checkboxes:
            return False
        try:
            checkboxes[0].click()
        except Exception:
            return False
        proceed_buttons = [
            b for b in driver.find_elements(By.XPATH, "//button[normalize-space(.)='Proceed']") if b.is_displayed()
        ]
        if proceed_buttons:
            try:
                proceed_buttons[0].click()
            except Exception:
                pass
        return True

    if find_and_click_here():
        progress("Solved an Akamai \"I'm not a robot\" challenge (top-level document)")
        return True

    for frame in driver.find_elements(By.TAG_NAME, "iframe"):
        try:
            driver.switch_to.frame(frame)
            if find_and_click_here():
                progress("Solved an Akamai \"I'm not a robot\" challenge (iframe)")
                return True
        except Exception:
            pass
        finally:
            driver.switch_to.default_content()
    return False


def resolve_service_tag_slug(
    driver,
    service_tag: str,
    locale: str = DEFAULT_LOCALE,
    attempts: int = 3,
    poll_timeout: float = 30,
    debug: bool = False,
) -> str:
    """Look up a service tag via a product overview page's "Identify a
    product" widget and return the resolved product slug (e.g.
    "poweredge-r630") for use with TYPE_URL_TEMPLATES. See the comment
    above SERVICE_TAG_INPUT_ID for how this works and its known gap (a tag
    that happens to belong to SERVICE_TAG_BASE_SLUG itself).
    """
    base_url = f"https://www.dell.com/support/product-details/{locale}/product/{SERVICE_TAG_BASE_SLUG}/overview"

    def submit_tag():
        field = driver.find_element(By.ID, SERVICE_TAG_INPUT_ID)
        field.click()
        field.send_keys(service_tag)
        time.sleep(1)
        try:
            driver.find_element(By.ID, SERVICE_TAG_SUBMIT_BUTTON_ID).click()
        except NoSuchElementException:
            field.send_keys(Keys.RETURN)  # fallback if the button isn't where expected

    for attempt in range(1, attempts + 1):
        progress(f"Looking up service tag '{service_tag}' (attempt {attempt}/{attempts})...")
        driver.get(base_url)
        dismiss_cookie_banner(driver, WebDriverWait(driver, 8))

        try:
            WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, SERVICE_TAG_INPUT_ID)))
        except TimeoutException:
            progress("Could not find the service tag field; retrying")
            continue

        submit_tag()
        if debug:
            time.sleep(2)
            save_debug_artifacts(driver, f"dell_debug_servicetag_attempt{attempt}_submitted")

        deadline = time.time() + poll_timeout
        challenged = False
        while time.time() < deadline:
            time.sleep(1)

            match = re.search(r"/product/([^/?#]+)", driver.current_url)
            if match and match.group(1) != SERVICE_TAG_BASE_SLUG:
                slug = match.group(1)
                progress(f"Service tag resolved to '{slug}'")
                return slug

            for error_id in SERVICE_TAG_ERROR_IDS:
                try:
                    el = driver.find_element(By.ID, error_id)
                except NoSuchElementException:
                    continue
                if el.is_displayed():
                    raise RuntimeError(f"Dell rejected service tag '{service_tag}': {el.text.strip()}")

            try:
                dialog = driver.find_element(By.ID, CHANGE_PRODUCT_DIALOG_ID)
                if dialog.is_displayed() and dialog.text.strip():
                    try:
                        dialog.find_element(
                            By.XPATH, ".//button[contains(translate(., 'CONTINUE', 'continue'), 'continue')]"
                        ).click()
                    except NoSuchElementException:
                        pass
                    continue
            except NoSuchElementException:
                pass

            if try_solve_akamai_challenge(driver):
                challenged = True
                if debug:
                    save_debug_artifacts(driver, f"dell_debug_servicetag_attempt{attempt}_after_challenge")
                # the challenge likely swallowed the original search request;
                # resubmit it once the interstitial is gone.
                try:
                    submit_tag()
                except NoSuchElementException:
                    pass

        if debug:
            save_debug_artifacts(driver, f"dell_debug_servicetag_attempt{attempt}_timeout")
        progress(
            f"Attempt {attempt} timed out without resolving the service tag"
            + (" (after solving a challenge)" if challenged else "")
        )

    raise RuntimeError(
        f"Could not resolve service tag '{service_tag}' after {attempts} attempts. Dell's Akamai bot "
        "protection intermittently blocks this specific lookup for automated browser sessions - this "
        "was confirmed during testing, most attempts get a silent failure with no visible error, "
        "occasionally an 'I'm not a robot' checkbox challenge appears (which this script solves "
        "automatically when it does; switching --engine doesn't reliably help here - confirmed by "
        "testing that this specific lookup still gets blocked most of the time even via Firefox, "
        "which otherwise gets through on pages Chrome can't). Try again, or look the tag up yourself "
        f"once at {base_url} and pass the resulting model name to --model instead."
    )


def find_cards(driver) -> List:
    return driver.find_elements(By.CSS_SELECTOR, ROW_SELECTOR)


def cell_text(gridcells: List, index: int) -> Optional[str]:
    if index >= len(gridcells):
        return None
    return gridcells[index].text.strip() or None


def scrape_cards(rows: List, category: str) -> List[DriverInfo]:
    results = []
    for row in rows:
        gridcells = row.find_elements(By.CSS_SELECTOR, GRIDCELL_SELECTOR)
        if len(gridcells) <= COL_NAME:
            continue

        download_url = None
        try:
            link = gridcells[COL_ACTION].find_element(By.CSS_SELECTOR, "a[href]")
            download_url = link.get_attribute("href")
        except (NoSuchElementException, IndexError):
            pass

        results.append(
            DriverInfo(
                name=cell_text(gridcells, COL_NAME) or "Unknown",
                category=cell_text(gridcells, COL_CATEGORY) or category,
                release_date=cell_text(gridcells, COL_DATE),
                importance=cell_text(gridcells, COL_IMPORTANCE),
                download_url=download_url,
            )
        )
    return results


def find_manual_rows(driver) -> List:
    return driver.find_elements(By.CSS_SELECTOR, MANUAL_ROW_SELECTOR)


def scrape_manuals(rows: List) -> List[ManualInfo]:
    results = []
    for row in rows:
        try:
            link = row.find_element(By.CSS_SELECTOR, "a.manual-link")
        except NoSuchElementException:
            continue

        doc_type = None
        try:
            doc_type = row.find_element(By.CSS_SELECTOR, "div.dds__body-2").text.strip() or None
        except NoSuchElementException:
            pass

        updated = None
        try:
            updated_text = row.find_element(By.CSS_SELECTOR, ".updated-id").text
            updated = updated_text.split(":", 1)[-1].strip() or None
        except NoSuchElementException:
            pass

        results.append(
            ManualInfo(
                title=" ".join(link.text.split()) or "Unknown",
                url=link.get_attribute("href"),
                doc_type=doc_type,
                updated=updated,
            )
        )
    return results


def find_article_rows(driver) -> List:
    return driver.find_elements(By.CSS_SELECTOR, ARTICLE_ROW_SELECTOR)


def scrape_articles(rows: List) -> List[ArticleInfo]:
    results = []
    for row in rows:
        try:
            link = row.find_element(By.CSS_SELECTOR, "a.article-link")
        except NoSuchElementException:
            continue

        description = None
        try:
            description = row.find_element(By.CSS_SELECTOR, "div.dds__body-2").text.strip() or None
        except NoSuchElementException:
            pass

        updated = None
        try:
            updated = row.find_element(By.CSS_SELECTOR, ".updated-id .dds__ml-0").text.split(":", 1)[-1].strip() or None
        except NoSuchElementException:
            pass

        article_id = None
        try:
            article_id = row.find_element(By.CSS_SELECTOR, ".updated-id .dds__ml-4").text.split(":", 1)[-1].strip() or None
        except NoSuchElementException:
            article_id = link.get_attribute("data-articlenumber") or None

        results.append(
            ArticleInfo(
                title=" ".join(link.text.split()) or "Unknown",
                url=link.get_attribute("href"),
                description=description,
                updated=updated,
                article_id=article_id,
            )
        )
    return results


def find_video_rows(driver) -> List:
    return driver.find_elements(By.CSS_SELECTOR, VIDEO_ROW_SELECTOR)


def scrape_videos(rows: List) -> List[VideoInfo]:
    results = []
    for row in rows:
        title_link = None
        for link in row.find_elements(By.CSS_SELECTOR, "a.video-card-link"):
            if link.text.strip():
                title_link = link
                break
        if title_link is None:
            continue

        thumbnail_url = None
        try:
            thumbnail_url = row.find_element(By.CSS_SELECTOR, "img").get_attribute("src") or None
        except NoSuchElementException:
            pass

        body3 = row.find_elements(By.CSS_SELECTOR, "div.dds__body-3")
        date = body3[0].text.strip() or None if len(body3) > 0 else None
        duration = body3[1].text.strip() or None if len(body3) > 1 else None

        results.append(
            VideoInfo(
                title=" ".join(title_link.text.split()) or "Unknown",
                url=title_link.get_attribute("href"),
                date=date,
                duration=duration,
                thumbnail_url=thumbnail_url,
            )
        )
    return results


def find_advisory_rows(driver) -> List:
    return driver.find_elements(By.CSS_SELECTOR, ADVISORY_ROW_SELECTOR)


def scrape_advisories(rows: List) -> List[AdvisoryInfo]:
    results = []
    for row in rows:
        cells = row.find_elements(By.CSS_SELECTOR, ADVISORY_CELL_SELECTOR)
        if len(cells) <= ADV_COL_UPDATED:
            continue

        advisory_id = None
        url = None
        try:
            link = cells[ADV_COL_ID].find_element(By.CSS_SELECTOR, "a")
            advisory_id = link.text.strip() or None
            url = link.get_attribute("href")
        except NoSuchElementException:
            pass

        results.append(
            AdvisoryInfo(
                title=cell_text(cells, ADV_COL_TITLE) or "Unknown",
                advisory_id=advisory_id,
                url=url,
                impact=cell_text(cells, ADV_COL_IMPACT),
                last_updated=cell_text(cells, ADV_COL_UPDATED),
            )
        )
    return results


def find_regulatory_rows(driver) -> List:
    return driver.find_elements(By.CSS_SELECTOR, REGULATORY_ROW_SELECTOR)


def scrape_regulatory(rows: List) -> List[RegulatoryInfo]:
    results = []
    for row in rows:
        try:
            link = row.find_element(By.CSS_SELECTOR, "a.mfe-article-link")
        except NoSuchElementException:
            continue

        product = None
        regulatory_model = None
        regulatory_type = None
        for span in row.find_elements(By.CSS_SELECTOR, ".updated-id > span"):
            text = span.text.strip()
            if not text:
                continue
            lower = text.lower()
            if lower.startswith("regulatory model:"):
                regulatory_model = text.split(":", 1)[-1].strip() or None
            elif lower.startswith("regulatory type:"):
                regulatory_type = text.split(":", 1)[-1].strip() or None
            elif product is None:
                product = text

        results.append(
            RegulatoryInfo(
                title=" ".join(link.text.split()) or "Unknown",
                url=link.get_attribute("href"),
                product=product,
                regulatory_model=regulatory_model,
                regulatory_type=regulatory_type,
            )
        )
    return results


def save_debug_artifacts(driver, prefix: str) -> None:
    try:
        driver.save_screenshot(f"{prefix}.png")
        with open(f"{prefix}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"[debug] saved {prefix}.png / {prefix}.html", file=sys.stderr)
    except Exception as e:
        print(f"[debug] could not save artifacts for {prefix}: {e}", file=sys.stderr)


def progress(msg: str) -> None:
    print(f"[+] {msg}", file=sys.stderr, flush=True)


def scrape_drivers_page(driver, wait: WebDriverWait, category: str, os_filter: Optional[str], debug: bool) -> List[DriverInfo]:
    progress("Waiting for the driver list widget to render...")
    try:
        wait.until(EC.presence_of_element_located((By.ID, CATEGORY_TRIGGER_ID)))
    except TimeoutException:
        progress("Timed out waiting for the driver list widget (continuing anyway)")
    if debug:
        save_debug_artifacts(driver, "dell_debug_03_content")

    if os_filter:
        progress(f"Looking for the '{os_filter}' operating system filter...")
        os_applied = select_os(driver, os_filter, timeout=8)
        if not os_applied:
            progress(f"Could not find an '{os_filter}' operating system option; leaving OS filter as-is")
        else:
            progress(f"Applied '{os_filter}' operating system filter")
        if debug:
            save_debug_artifacts(driver, "dell_debug_04_after_os")

    progress(f"Looking for the '{category}' category filter...")
    applied = select_category(driver, category, timeout=8)
    if debug:
        save_debug_artifacts(driver, "dell_debug_05_after_category")
    if not applied:
        progress(f"Could not find a '{category}' filter control; scraping the unfiltered list instead")
    else:
        progress(f"Applied '{category}' filter")

    progress("Waiting for filtered results...")
    try:
        wait.until(lambda d: len(find_cards(d)) > 0)
    except TimeoutException:
        progress("Timed out waiting for result cards")

    cards = find_cards(driver)
    progress(f"Found {len(cards)} candidate driver card(s)")
    if not cards and debug:
        save_debug_artifacts(driver, "dell_debug_06_no_cards")

    return scrape_cards(cards, category)


def scrape_manuals_page(driver, wait: WebDriverWait, debug: bool) -> List[ManualInfo]:
    progress("Waiting for the manuals list to render...")
    try:
        wait.until(lambda d: len(find_manual_rows(d)) > 0)
    except TimeoutException:
        progress("Timed out waiting for the manuals list")
    if debug:
        save_debug_artifacts(driver, "dell_debug_03_content")

    rows = find_manual_rows(driver)
    progress(f"Found {len(rows)} manual(s)")
    if not rows and debug:
        save_debug_artifacts(driver, "dell_debug_06_no_cards")

    return scrape_manuals(rows)


def scrape_articles_page(driver, wait: WebDriverWait, debug: bool) -> List[ArticleInfo]:
    progress("Waiting for the articles list to render...")
    try:
        wait.until(lambda d: len(find_article_rows(d)) > 0)
    except TimeoutException:
        progress("Timed out waiting for the articles list")
    if debug:
        save_debug_artifacts(driver, "dell_debug_03_content")

    rows = find_article_rows(driver)
    progress(f"Found {len(rows)} article(s) (Dell caps the public/signed-out view at 30, even if more exist)")
    if not rows and debug:
        save_debug_artifacts(driver, "dell_debug_06_no_cards")

    return scrape_articles(rows)


def scrape_videos_page(driver, wait: WebDriverWait, debug: bool) -> List[VideoInfo]:
    progress("Waiting for the videos list to render...")
    try:
        wait.until(lambda d: len(find_video_rows(d)) > 0)
    except TimeoutException:
        progress("Timed out waiting for the videos list")
    if debug:
        save_debug_artifacts(driver, "dell_debug_03_content")

    rows = find_video_rows(driver)
    progress(f"Found {len(rows)} video(s)")
    if not rows and debug:
        save_debug_artifacts(driver, "dell_debug_06_no_cards")

    return scrape_videos(rows)


def scrape_advisories_page(driver, wait: WebDriverWait, debug: bool, impact: Optional[str] = None) -> List[AdvisoryInfo]:
    progress("Waiting for the advisories list to render...")
    try:
        wait.until(lambda d: len(find_advisory_rows(d)) > 0)
    except TimeoutException:
        progress("Timed out waiting for the advisories list")
    if debug:
        save_debug_artifacts(driver, "dell_debug_03_content")

    if impact:
        progress(f"Looking for the '{impact}' Impact filter...")
        applied = select_impact(driver, impact, timeout=8)
        if not applied:
            progress(f"Could not apply '{impact}' Impact filter; returning all advisories instead")
        else:
            progress(f"Applied '{impact}' Impact filter")
        if debug:
            save_debug_artifacts(driver, "dell_debug_04_after_impact")

    rows = find_advisory_rows(driver)
    progress(f"Found {len(rows)} advisory(ies) (Security tab only; Technical tab isn't fetched)")
    if not rows and debug:
        save_debug_artifacts(driver, "dell_debug_06_no_cards")

    return scrape_advisories(rows)


def scrape_regulatory_page(driver, wait: WebDriverWait, debug: bool) -> List[RegulatoryInfo]:
    progress("Waiting for the regulatory list to render...")
    try:
        wait.until(lambda d: len(find_regulatory_rows(d)) > 0)
    except TimeoutException:
        progress("Timed out waiting for the regulatory list")
    if debug:
        save_debug_artifacts(driver, "dell_debug_03_content")

    rows = find_regulatory_rows(driver)
    progress(f"Found {len(rows)} regulatory document(s)")
    if not rows and debug:
        save_debug_artifacts(driver, "dell_debug_06_no_cards")

    return scrape_regulatory(rows)


def run_scrape(
    url: str,
    category: str,
    os_filter: Optional[str] = "BIOS",
    page_type: str = DEFAULT_TYPE,
    headless: bool = False,
    debug: bool = False,
    chrome_binary: Optional[str] = None,
    engine: str = "uc",
    impact: Optional[str] = None,
    service_tag: Optional[str] = None,
    locale: str = DEFAULT_LOCALE,
    firefox_binary: Optional[str] = None,
    geckodriver_binary: Optional[str] = None,
) -> List:
    if engine == "uc":
        driver = build_driver_uc(headless=headless, chrome_binary=chrome_binary)
    elif engine == "firefox":
        driver = build_driver_firefox(
            headless=headless, firefox_binary=firefox_binary, geckodriver_binary=geckodriver_binary
        )
    else:
        driver = build_driver(headless=headless, chrome_binary=chrome_binary)
    wait = WebDriverWait(driver, 15)
    try:
        if service_tag:
            slug = resolve_service_tag_slug(driver, service_tag, locale, debug=debug)
            url = TYPE_URL_TEMPLATES[page_type].format(slug=slug, locale=locale)

        progress(f"Opening {url}")
        driver.get(url)
        if debug:
            save_debug_artifacts(driver, "dell_debug_01_loaded")

        progress("Dismissing cookie banner (if present)...")
        dismiss_cookie_banner(driver, WebDriverWait(driver, 8))
        if debug:
            save_debug_artifacts(driver, "dell_debug_02_after_cookie")

        if page_type == "drivers":
            return scrape_drivers_page(driver, wait, category, os_filter, debug)
        elif page_type == "manuals":
            return scrape_manuals_page(driver, wait, debug)
        elif page_type == "articles":
            return scrape_articles_page(driver, wait, debug)
        elif page_type == "videos":
            return scrape_videos_page(driver, wait, debug)
        elif page_type == "advisories":
            return scrape_advisories_page(driver, wait, debug, impact)
        elif page_type == "regulatory":
            return scrape_regulatory_page(driver, wait, debug)
        else:
            progress(
                f"--type {page_type!r} has no filtering/scraping support yet; "
                "the page has been loaded but nothing will be extracted. "
                "Re-run with --debug and share dell_debug_02_after_cookie.html "
                "so support for this type can be added."
            )
            if debug:
                time.sleep(2)  # let any client-side rendering settle before the dump
                save_debug_artifacts(driver, "dell_debug_03_content")
            return []
    finally:
        driver.quit()


def default_download_directory(model_label: Optional[str]) -> str:
    """$HOME/firmware/<model_label>, normalized the same way --model
    normalizes a model name for a URL slug (lowercase, whitespace/hyphens
    collapsed) but without the "poweredge-" prefix assumption, since this
    is a local folder name, not a Dell URL.
    """
    label = re.sub(r"[\s/\\-]+", "-", (model_label or "product").strip().lower()).strip("-") or "product"
    return os.path.join(os.path.expanduser("~"), "firmware", label)


def download_file(url: str, directory: str) -> str:
    """Download `url` into `directory` (assumed to already exist - see
    download_results()) and return the local file path. Filename comes
    from the URL itself. Uses a browser-like User-Agent since some Dell
    CDN endpoints reject the default urllib one.
    """
    filename = os.path.basename(urllib.parse.urlparse(url).path)
    filename = urllib.parse.unquote(filename) or "download"
    dest_path = os.path.join(directory, filename)

    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response, open(dest_path, "wb") as f:
        shutil.copyfileobj(response, f)
    return dest_path


def download_results(results: List, directory: str) -> None:
    """Download each result's file (download_url if present, else url) into
    `directory`. Works well for direct file links (drivers, regulatory PDFs
    - typically hosted on dl.dell.com, which isn't behind the same Akamai
    protection as the www.dell.com pages), but a result whose only link is
    a www.dell.com webpage (advisories, articles, some manuals, videos)
    will likely 403 the same way plain `curl`/`requests` do against those
    pages elsewhere in this script - see the module docstring.
    """
    os.makedirs(directory, exist_ok=True)
    progress(f"Downloading {len(results)} file(s) to {directory}...")
    for result in results:
        url = getattr(result, "download_url", None) or getattr(result, "url", None)
        label = getattr(result, "name", None) or getattr(result, "title", None) or url
        if not url:
            progress(f"Skipping '{label}': no download URL")
            continue
        try:
            path = download_file(url, directory)
            progress(f"Downloaded '{label}' -> {path}")
        except (urllib.error.URLError, OSError) as e:
            progress(f"Failed to download '{label}': {e}")


def filter_by_search(results: List, search: Optional[str]) -> List:
    """Keep only results with `search` (case-insensitive) in any field's
    value. Works across every result type (DriverInfo, ManualInfo, ...)
    since it just checks all of a dataclass instance's field values,
    rather than needing per-type keyword-search selectors like the site's
    own "Filter by keyword" boxes would.
    """
    if not search:
        return results
    needle = search.lower()
    return [r for r in results if any(needle in str(v).lower() for v in asdict(r).values() if v is not None)]


def write_output(results: List, output: Optional[str]) -> None:
    rows = [asdict(r) for r in results]
    if not output:
        print(json.dumps(rows, indent=2))
        return
    if output.endswith(".csv"):
        with open(output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
            writer.writeheader()
            writer.writerows(rows)
    else:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2)
    print(f"Wrote {len(rows)} result(s) to {output}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s ({__long_name__}) {__version__}"
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Dell model to build the drivers URL for, e.g. R730. No default - one of "
        "--model/--url/--servicetag is required. Ignored if --url is also given.",
    )
    _unfiltered_types = ", ".join(sorted(SCRAPABLE_TYPES - {"drivers", "advisories"}))
    _unscrapable_types = ", ".join(sorted(set(TYPE_URL_TEMPLATES) - SCRAPABLE_TYPES))
    _type_help = (
        f"Product-support page to build the URL for (default: {DEFAULT_TYPE}). 'documents' is the same "
        "as 'manuals', and 'downloads' is the same as 'drivers'. Ignored if --url is also given. "
        "Category/OS filtering only applies to 'drivers' "
        "(--category/--os) and Impact filtering only to 'advisories' (--impact); "
        f"{_unfiltered_types} return their full listing with no filtering"
    )
    if _unscrapable_types:
        _type_help += f"; {_unscrapable_types} just navigate there with no scraping support yet"
    _type_help += "."
    parser.add_argument(
        "--type",
        dest="page_type",
        default=DEFAULT_TYPE,
        choices=sorted(set(TYPE_URL_TEMPLATES) | set(TYPE_ALIASES)),
        help=_type_help,
    )
    parser.add_argument(
        "--locale",
        default=DEFAULT_LOCALE,
        help=f"Locale segment of the URL, e.g. en-au, en-us (default: {DEFAULT_LOCALE}). Ignored if --url is given.",
    )
    parser.add_argument("--url", help="Dell product-support page URL (overrides --model/--type/--locale)")
    parser.add_argument(
        "--geturl",
        action="store_true",
        help="Just print the constructed URL (from --model/--type/--locale, or --url) and exit - no "
        "browser, no network activity. Not compatible with --servicetag, since resolving a tag "
        "requires actually querying Dell.",
    )
    parser.add_argument(
        "--servicetag",
        help="Look up this service tag on Dell's support home page (Identify a product) and use the "
        "resulting product for --type/--category/etc., instead of guessing a slug from --model. "
        "Overrides --model and --url. CONFIRMED WORKING BUT INTERMITTENT: Dell's Akamai bot "
        "protection blocks this specific lookup for automated sessions more often than not - most "
        "attempts fail silently, and this script retries a few times and auto-solves an 'I'm not a "
        "robot' checkbox challenge if Akamai shows one, but it can still fail outright.",
    )
    parser.add_argument(
        "--category", "--cat", dest="category", default="BIOS", help="Driver category to filter on (default: BIOS)"
    )
    parser.add_argument(
        "--os",
        dest="os_filter",
        default="BIOS",
        help="Operating System filter to select (default: BIOS, Dell's OS-agnostic "
        "bucket for BIOS/firmware updates). Pass --os none to leave Dell's own "
        "default OS selection untouched.",
    )
    parser.add_argument(
        "--impact",
        default=None,
        help="Impact filter to select, only used with --type advisories (e.g. Critical, High, "
        "Medium, Low). If not set, all advisories are returned regardless of impact.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chrome headless. Off by default: Dell's Akamai bot protection has "
        "reliably blocked headless requests in testing, while a visible browser gets through.",
    )
    parser.add_argument(
        "--search",
        help="Only return results containing this string (case-insensitive, matched against "
        "every field of a result, e.g. title/description/category). Applied after scraping, "
        "on top of whatever --type/--category/--os/--impact filtering already narrowed it to. "
        "If not set, all scraped results are returned.",
    )
    parser.add_argument("--debug", action="store_true", help="Save a screenshot/HTML dump if no results are found")
    parser.add_argument("--output", help="Write results to this file (.json or .csv) instead of stdout")
    parser.add_argument(
        "--download",
        action="store_true",
        help="Actually download each result's file into --directory, in addition to the usual JSON/CSV "
        "output. Works well for direct file links (drivers, regulatory PDFs); a result whose only link "
        "is a www.dell.com webpage (advisories, articles, some manuals, videos) will likely fail the "
        "same way plain curl/requests do against those pages elsewhere in this script.",
    )
    parser.add_argument(
        "--directory",
        help="Directory to download files into when --download is given (default: "
        "$HOME/firmware/<model>, where <model> is --model or --servicetag, normalized).",
    )
    parser.add_argument("--chrome-binary", help="Path to a Chrome/Chromium binary, if auto-detection fails")
    parser.add_argument(
        "--firefox-binary",
        help="Path to a Firefox binary, if auto-detection fails. Must NOT be a snap install - "
        "confirmed by testing that snap Firefox cannot be automated at all.",
    )
    parser.add_argument("--geckodriver-binary", help="Path to a geckodriver binary, if auto-detection fails")
    parser.add_argument(
        "--engine",
        choices=["selenium", "uc", "firefox"],
        default="uc",
        help="Browser automation backend (default: uc). 'uc' uses undetected-chromedriver, "
        "which patches the chromedriver binary itself instead of just setting Selenium options - "
        "worth trying if --headless keeps getting blocked. Requires: pip install undetected-chromedriver. "
        "'selenium' is plain Selenium/Chrome, no extra dependency. "
        "'firefox' uses Firefox instead of Chrome entirely - confirmed by testing to get through on a "
        "URL that was blocking Chrome (both other engines) outright in the same environment; needs a "
        "non-snap Firefox + geckodriver (see --firefox-binary).",
    )
    args = parser.parse_args()
    if not args.model and not args.url and not args.servicetag:
        parser.print_usage(sys.stderr)
        print(f"{parser.prog}: error: one of --model, --url, or --servicetag is required", file=sys.stderr)
        sys.exit(2)

    os_filter = None if args.os_filter.lower() == "none" else args.os_filter
    args.page_type = normalize_type(args.page_type)
    # When --servicetag is given without --model/--url, run_scrape() resolves
    # the real url itself before ever using this placeholder.
    url = args.url or (build_product_url(args.model, args.page_type, args.locale) if args.model else "")

    if args.geturl:
        if not url:
            print(
                "Error: --geturl needs --model or --url; --servicetag can't be resolved to a URL "
                "without actually querying Dell (which --geturl doesn't do).",
                file=sys.stderr,
            )
            sys.exit(1)
        print(url)
        sys.exit(0)

    try:
        results = run_scrape(
            url,
            args.category,
            os_filter=os_filter,
            page_type=args.page_type,
            headless=args.headless,
            debug=args.debug,
            chrome_binary=args.chrome_binary,
            engine=args.engine,
            impact=args.impact,
            service_tag=args.servicetag,
            locale=args.locale,
            firefox_binary=args.firefox_binary,
            geckodriver_binary=args.geckodriver_binary,
        )
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not results:
        if args.page_type not in SCRAPABLE_TYPES:
            sys.exit(1)  # already explained by run_scrape's progress message
        print(f"No '{args.category}' {args.page_type} found.", file=sys.stderr)
        sys.exit(1)

    if args.search:
        before = len(results)
        results = filter_by_search(results, args.search)
        progress(f"Filtered to {len(results)} of {before} result(s) containing '{args.search}'")
        if not results:
            print(f"No results contained '{args.search}'.", file=sys.stderr)
            sys.exit(1)

    write_output(results, args.output)

    if args.download:
        directory = args.directory or default_download_directory(args.model or args.servicetag)
        download_results(results, directory)


if __name__ == "__main__":
    main()
