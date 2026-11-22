# SIMBAD outage and the mirror fallback

Evidence behind the mirror fallback rules in `CLAUDE.md`. Gathered on 2026-11-20 with pyvo 1.10.0 and astroquery 0.4.11 (the latest releases on PyPI that day), on the x86_64 container on the Arch host.

## The outage

- CDS (Strasbourg) has a cybersecurity incident and took its servers offline on purpose. The announcement on `https://simbad.cds.unistra.fr/` ("Last updated November 09, 2026") and `https://cds.unistra.fr/` ("Last updated November 18, 2026") gives no cause and no restore date. Both pages list the fallbacks.
- Start date: CDS doesn't state one. The earliest public reports found are from 28–30 Oct 2026, for example skyfielders/python-skyfield#1155, opened 2026-10-30 about `cdsarc.cds.unistra.fr` not answering. astropy/astroquery#3701 ("CDS Mirrors") was opened 2026-11-02 and merged 2026-11-12. Its commit `a3a96d5` (2026-11-03) added `simbad.idia.ac.za` to `servers_list`, and that's not in any release yet.
- On 2026-11-20 every path on `simbad.cds.unistra.fr` returned HTTP 404 with a CDS "Page unavailable" HTML page (Last-Modified 2026-11-10), over both http and https. That included `/simbad/`, `/simbad/sim-tap/sync`, `/simbad/sim-tap/capabilities`, and the old app URL `…/sim-tap/sync/sync`. By 2026-11-22 it no longer accepted connections at all, see the connect timeout section below.
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

## CDS stopped answering: the connect timeout (2026-11-22)

Measured on 2026-11-22 with pyvo 1.10.0, astroquery 0.4.11, requests 2.34.2 and urllib3 2.8.0, on the x86_64 container on the Arch host.

- The 404 from 2026-11-20 is gone. `simbad.cds.unistra.fr` still resolves (a CNAME to `www-cds.cds.unistra.fr`, 130.79.129.14, no AAAA record), but a TCP connect on 443 or on 80 never completes. curl `--max-time 40` ended with exit 28 and `time_connect=0`. In the meantime the mirrors connected in 0.11 s (`simbad.cfa.harvard.edu`), 0.13 s (`simbad.harvard.edu`) and 0.24 s (IDIA, after a 0.69 s DNS lookup), and the whole `/capabilities` request took 0.32/0.34/1.43 s.
- Without a timeout, a plain `TAPService(cds).search(…)` raised `DALFormatError: ConnectTimeout` after **136.4 s**. That is the kernel's SYN retransmissions (`net.ipv4.tcp_syn_retries = 6` here). Other OSes give up after a different time.
- Nobody sets a network timeout. pyvo's `TAPQuery.submit` (`session.post(url, data=…, stream=True, files=…)`) and the VOSI GET in `vosi.py` pass none, and requests has no session-level default. astroquery's `Simbad.timeout` / `conf.timeout` (1080) is `execution_duration` for async jobs, a server-side limit, not a network timeout. `Simbad.tap` builds `TAPService(baseurl=…, session=self._session)`, and `_session` is a `requests.Session` from `BaseQuery` in 0.4.6, 0.4.7 and 0.4.11 alike.
- urllib3 applies the connect part of a `(connect, read)` pair to the TCP connect, the TLS handshake and sending the request (`conn.timeout = connect_timeout`, `connectionpool.py` line 465). It switches to the read part only before waiting for the response (line 536). `HTTPAdapter`'s default `max_retries` is 0, so a connect timeout is not retried. DNS resolution is not covered by either part.
- Measured with the implementation, from the built wheel:
  - With 5 s, CDS failed after 5.01 s. The TAP query raised `DALFormatError: ConnectTimeout … (connect timeout=5)`. The first SIMBAD-window lookup raised `DALServiceError: Unable to access the capabilities endpoint …`, and the second raised `DALFormatError` from `/sync`, because astroquery caches `Simbad._hardlimit` after the first mirror answers.
  - Every fallback took 5.1–5.5 s in total: the TAP example, a bad ADQL query (still `DALQueryError` from Harvard, IDIA not tried) and two "Vega" lookups (65 IDs).
- The main-server-only rule was checked three ways:
  - a single-server `[cds]` list was still waiting after 15 s;
  - CDS placed second of three (as a mirror) was still waiting after 15 s;
  - a fake `attempt` saw the ContextVar as `[5, None, None]` for three servers and `[None]` for one, and `None` again after a success, a fallback and an escaping `ValueError`.
- The read side stays unlimited: a heavy `COUNT(*)` join sent to Harvard with the 5 s limit in force ran until Harvard's own gateway answered `504 Gateway Time-out` at 60.3 s. So Harvard's sync endpoint has a gateway limit of about 60 s, and a 504 is a `DALServiceError` that falls back to the next mirror.

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
