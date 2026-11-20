# SIMBAD outage and the mirror fallback

Evidence behind the mirror fallback rules in `CLAUDE.md`. Gathered on 2026-11-20 with pyvo 1.10.0 and astroquery 0.4.11 (the latest releases on PyPI that day), on the x86_64 container on the Arch host.

## The outage

- CDS (Strasbourg) has a cybersecurity incident and took its servers offline on purpose. The announcement on `https://simbad.cds.unistra.fr/` ("Last updated November 09, 2026") and `https://cds.unistra.fr/` ("Last updated November 18, 2026") gives no cause and no restore date. Both pages list the fallbacks.
- Start date: CDS doesn't state one. The earliest public reports found are from 28–30 Oct 2026, for example skyfielders/python-skyfield#1155, opened 2026-10-30 about `cdsarc.cds.unistra.fr` not answering. astropy/astroquery#3701 ("CDS Mirrors") was opened 2026-11-02 and merged 2026-11-12. Its commit `a3a96d5` (2026-11-03) added `simbad.idia.ac.za` to `servers_list`, and that's not in any release yet.
- On 2026-11-20 every path on `simbad.cds.unistra.fr` returns HTTP 404 with a CDS "Page unavailable" HTML page (Last-Modified 2026-11-10), over both http and https. That includes `/simbad/`, `/simbad/sim-tap/sync`, `/simbad/sim-tap/capabilities`, and the old app URL `…/sim-tap/sync/sync`.
- The mirrors, both official and listed by CDS:
  - CfA Harvard: `https://simbad.cfa.harvard.edu/simbad/sim-tap/`, "data ingested up to 2026-10-14". `simbad.harvard.edu` serves the same over https directly, while `http://simbad.cfa.harvard.edu` answers with a 301 to https.
  - IDIA (South Africa): `https://simbad.idia.ac.za/simbad/sim-tap/`.

  Both answer sync queries (`QUERY_STATUS` OK). All four SIMBAD examples return the same row counts on both, 31/67/1/3.

## The old URL

`examples.py` had `http://simbad.cds.unistra.fr/simbad/sim-tap/sync`. PyVO's `TAPQuery.queryurl` is `f'{baseurl}/{mode}'`, so the request went to `…/sim-tap/sync/sync`, which CDS used to tolerate. Harvard tolerates it too. The URL is now the base `https://simbad.cds.unistra.fr/simbad/sim-tap`. The https scheme is what astroquery ≥ 0.4.8 uses for CDS (`tap_url = f"https://{self.server}/simbad/sim-tap"`), but it couldn't be checked against CDS itself while it's down.

## Which exceptions mean "server unavailable" (pyvo 1.10.0)

The hierarchy: `DALAccessError` ← `DALProtocolError` ← `DALServiceError` (← `DALRateLimitError`, `DALJobTimeoutError`) and `DALFormatError`. `DALQueryError` is directly under `DALAccessError`. All of them are importable from `pyvo.dal`. Measured outcomes:

- CDS 404 on a TAP query: `DALServiceError: 404 Client Error: Not Found for url: https://simbad.cds.unistra.fr/simbad/sim-tap/sync`.
- CDS 404 from astroquery's `query_objectids`: `DALServiceError: Unable to access the capabilities endpoint at: …` (multi-line). astroquery's `query_tap` checks `hardlimit` first, which fetches VOSI capabilities, and pyvo's VOSI code wraps `HTTPError`, `ConnectionError` and `Timeout` into `DALServiceError`. On the second call the error came from `/sync` instead.
- Unresolvable host on a TAP query: **`DALFormatError: ConnectionError: …`**, not `DALServiceError`. `execute_stream` calls `submit()` outside its `try`, so the raw `requests.ConnectionError` reaches `execute_votable`, which wraps any non-DAL exception into `DALFormatError`. The first version of the fallback caught only `DALServiceError` and `OSError`, and this case slipped through. That's why it catches `DALProtocolError`.
- Bad ADQL (an unknown column): SIMBAD answers HTTP 400 with an ERROR VOTable, and pyvo raises `DALQueryError` ("Incorrect ADQL query: 1 unresolved identifiers …"). So it isn't retried, and the fallback stopped at Harvard without trying IDIA.
- `requests.RequestException` subclasses `IOError`/`OSError`, so `OSError` catches any raw `requests` error that some other pyvo path lets through.

## astroquery's SIMBAD servers

- 0.4.8–0.4.11: `conf.servers_list = ['simbad.cds.unistra.fr', 'simbad.harvard.edu']`. The `Simbad.server` setter raises `ValueError` for anything not in `conf.servers_list`, and `SimbadClass.__init__` takes `conf.server`. On main (2026-11-10), IDIA has been added, plus `find_mirror=`/`find_fastest_mirror()` and a `simbad_server=` constructor argument, all unreleased.
- `conf.server` is a list-option `ConfigItem`, so astropy only accepts values from the list. CDS's fallback page suggests `server = simbad.cfa.harvard.edu` in `astroquery.cfg`, which isn't in the 0.4.11 list, so that config can't reach the app's code without failing inside astroquery first.
- Before 0.4.8 astroquery used the sim-script interface and had no `server` property. Setting it is inert there, and its errors aren't pyvo ones, so there's no fallback: it fails as before.

## Verification on 2026-11-20

- `ruff check` and `ty check` pass.
- The wheel was built with `uv build`, then a `python -I` script ran in `uv run --isolated --no-project --with <whl>`:
  - All four SIMBAD examples fell back from CDS to Harvard (a WARNING, then an INFO).
  - The bad query raised `DALQueryError` from Harvard.
  - `tryMirrors(["https://nonexistent.invalid/tap", harvard], …)` fell back.
  - An unknown URL got `[]`, and a trailing `/` still matched.
  - The SIMBAD window path ran twice for "Vega": CDS was tried first both times, and Harvard returned 65 IDs in column `id`.
- Real GUI on Xvfb (recipe in `dearpygui.md`), normal mode without `--debug`. The SIMBAD example query filled the results table while the service field kept the CDS URL. The SIMBAD window listed Vega's IDs. stdout showed the `[WARNING] … falling back to …` and `[INFO] Got results from the mirror …` lines.
- Harness gotcha: frame callbacks run on Dear PyGui's callback thread, so a blocking `executeQuery()` or `getSimbadIDs()` delays the callbacks queued after it. They then fire back to back, and a save followed by `stop_dearpygui` at fixed frame numbers loses the frame. Chain each step from the previous one with `dpg.set_frame_callback(dpg.get_frame_count() + 10, next)`.
