# TODO

Status: `[ ]` open, `[~]` in progress, `[x]` done.

## Open

- [ ] Add the current version (0.5.2) to the Versioning section of `CLAUDE.md` (note it must be updated on every version bump, or drop the idea if it goes stale too easily).
- [ ] Add a smoke-check script running the no-browser checks (`python3 -m py_compile dwelf.py`, `--version`, `--list types`, `--geturl --model R630 --type manuals`, `--checkconfig`), and document it in the Commands section of `CLAUDE.md` as the closest thing to a single test.
- [ ] Decide whether to add a `bsk` engine to `dwelf.py` (new external CLI + browser extension; uses snapshot refs because the challenge is in an iframe). Viable per 0.5.7; needs repeat runs first.
- [ ] Find out whether Akamai's denial of the direct `servicetag/<tag>` URL (0.6.4) is temporary/rate-based: retry later, try backoff, and consider reading the slug from a denied-free page; test `--engine firefox` (needs `geckodriver`).
- [ ] Investigate the intermittent `--engine uc` `web view not found` crash (0.6.4).

## Done

- [x] Use the direct `servicetag/<tag>/<type>` URL for `--servicetag`/`--specs`, widget as fallback (0.6.3).
- [x] Make `find_chrome_binary()` find Chrome on macOS (0.6.2).
- [x] Fix the `EC.attribute_to_be` crash in `run_specs()` (0.6.1).
- [x] Live-test `--engine attach` (0.5.3): `--servicetag C2P**** --specs` was still blocked by Akamai (0.5.4).
