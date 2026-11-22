# User-Agent

Evidence behind the User-Agent rules in `CLAUDE.md`. Gathered on 2026-11-22 with pyvo 1.10.0, astroquery 0.4.11, astropy 8.0.3 and requests 2.34.2 on Python 3.14.7 (what `uv run --isolated` picked), in the x86_64 container on the Arch host.

## Before the change

- TAP queries: `pyVO/1.10.0 Python/3.x.y (Linux) (IVOA-science)`. `pyvo.utils.http.create_session()` is a plain `requests.Session()` with `headers['User-Agent'] = USER_AGENT`, a module global that `setup_user_agent()` builds at import from `"pyVO/{pyvo_version} Python/{python_version} ({system}) (IVOA-{purpose})"`.
- SIMBAD window: `astroquery/0.4.11 pyVO/1.10.0 Python/3.x.y (Linux) python-requests/2.34.2`. `SimbadClass` derives only from `BaseVOQuery`, whose `__init__` makes a plain `requests.Session()` (so `python-requests/…`) and prepends `astroquery/{version} pyVO/{version} Python/… (system)`. `Simbad.tap` hands that `_session` to its `TAPService`, so the `/capabilities` GET (for `hardlimit`) and the `/sync` POST both use it.
- astropy's own downloads (`astropy.utils.data.download_file`, used by `astropy.utils.iers`): `astropy`, from `astropy.utils.data.conf.default_http_user_agent`. These are urllib requests, not `requests` sessions. The bundled tables now come from the separate `astropy-iers-data` package (0.2026.11.16 here). When exactly astropy downloads newer ones was not measured. The user decided to leave these requests out.

## PyVO's API for it

`setup_user_agent(*, purpose="science", primary_component="")` is in `pyvo.utils.http.__all__`. Its docstring asks for `primary_component` "preferably in the form "myProgram/0.2"" and puts it in front: `USER_AGENT = primary_component+" "+USER_AGENT`. It also says that an arbitrary string may be put into `pyvo.utils.http.USER_AGENT`. `create_session()` reads the global on each call. That's why `useragent.py` calls it at import and copies the result into `userAgent`.

## Why not in `version.py`

`setup.cfg` reads the version with `attr: tap_adql_sandbox.version.__version__`. setuptools' `read_attr` (`setuptools/config/expand.py`) tries `ast.literal_eval` first and executes the module only when that fails. `__version__` is `".".join(map(str, __version_info__))`, so it does execute `version.py`, in the isolated build environment, where pyvo isn't installed.

## After the change, measured from the built wheel

- `userAgent` = `tap-adql-sandbox/2026.11.22 pyVO/1.10.0 Python/3.14.7 (Linux) (IVOA-science)`.
- A local header-logging `http.server` got exactly that on `POST /tap/sync`, both from `TAPService(url, session=addConnectTimeout(addUserAgent(create_session())))` and from a `TAPService(url)` with no session (PyVO's own default one).
- A response hook on `Simbad._session` during a "Vega" lookup through `tryMirrors` (CDS failed to connect, Harvard returned 65 IDs) saw the same string on `GET …/sim-tap/capabilities` and `POST …/sim-tap/sync` to `simbad.harvard.edu`.
- Cloudflare's WAF at NASA Exoplanet Archive, whose bot scoring could depend on the User-Agent, let every `tapServices["nasa"]` example through with the new string (46, 355, 1, 1, 10 and 4 rows). The first example of PADC (44 rows), Gaia (247) and SIMBAD-TAP (31, by the Harvard fallback after the 5 s connect timeout) passed as well.
