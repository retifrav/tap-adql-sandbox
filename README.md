# TAP ADQL sandbox

<!-- MarkdownTOC -->

- [About](#about)
    - [Demonstration](#demonstration)
- [Installing](#installing)
    - [From PyPI](#from-pypi)
    - [From sources](#from-sources)
- [Running](#running)
- [Platforms](#platforms)
- [Known problems](#known-problems)
    - [Installation fails on a too new Python version](#installation-fails-on-a-too-new-python-version)
    - [Application tries to connect to remote hosts on startup and sometimes crashes](#application-tries-to-connect-to-remote-hosts-on-startup-and-sometimes-crashes)
    - [Queries might fail with UnicodeDecodeError](#queries-might-fail-with-unicodedecodeerror)
    - [SIMBAD at CDS is unavailable since October 2026](#simbad-at-cds-is-unavailable-since-october-2026)
    - [Queries might be blocked with 403 Forbidden](#queries-might-be-blocked-with-403-forbidden)
    - [NASA Exoplanet Archive no longer accepts WITH and subqueries in FROM](#nasa-exoplanet-archive-no-longer-accepts-with-and-subqueries-in-from)
- [3rd-party](#3rd-party)
    - [Dependencies](#dependencies)
    - [Resources](#resources)
- [Donation](#donation)

<!-- /MarkdownTOC -->

## About

A sandbox application for executing ADQL queries via TAP interface of various data sources, such as astronomical databases. Essentially, it's just a GUI for [PyVO](https://pypi.org/project/pyvo/).

![TAP ADQL sandbox application window](https://raw.githubusercontent.com/retifrav/tap-adql-sandbox/master/misc/screenshot-main-macos.png "TAP ADQL sandbox")

More details in [this article](https://decovar.dev/blog/2022/02/26/astronomy-databases-tap-adql/).

### Demonstration

https://user-images.githubusercontent.com/6904927/154367260-db2dc02c-ee88-4fe2-b500-cae14d51bd08.mp4

## Installing

### From PyPI

``` sh
$ pip install tap-adql-sandbox
```

### From sources

``` sh
$ cd /path/to/repository/
$ pip install ./
```

or:

``` sh
$ cd /path/to/repository/
$ python -m build
$ pip install ./dist/tap_adql_sandbox-VERSION-py3-none-any.whl
```

## Running

``` sh
$ tap-adql-sandbox
```

On GNU/Linux the application scales its window, fonts and controls by the content scale of the display, because Dear PyGui doesn't do that on its own (*not in the current version `2.3.1`*). The scale is `Xft.dpi` divided by 96, the same value that Qt and GTK applications use on X11. If the result is too big or too small (*for example, if Wayland compositor already upscales X11 applications*), you can set the scaling factor explicitly:

``` sh
$ tap-adql-sandbox --ui-scale 1.5
```

To see all the options:

``` sh
$ tap-adql-sandbox --help
```

## Platforms

Tested on all the major desktop operating systems (*Mac OS, Windows, GNU/Linux*), but latest versions of the application require Dear PyGui `2.3` or later, which is published only for these platforms:

- Mac OS 13 or newer, ARM64 (*Apple silicon*) only;
- Windows 10/11, x64 only;
- GNU/Linux, both x64 and ARM64.

which unfortunately applies the same restriction on the application itself.

Previous releases also supported x64 on older Mac OS, so if you need that, then you can try installing [0.8.2](https://pypi.org/project/tap-adql-sandbox/0.8.2/) release.

## Known problems

### Installation fails on a too new Python version

Some dependencies such as Dear PyGui are published only as pre-built wheels (*with no source package to build from*), and wheels for latest Python versions might appear only after some time. Until then, installing this application into an environment such a Python version may fail:

``` sh
ERROR: Could not find a version that satisfies the requirement dearpygui>=1.5.0 (from versions: none)
ERROR: No matching distribution found for dearpygui>=1.5.0
```

or, with `uv pip install`:

``` sh
hint: You require CPython 3.15 (`cp315`), but we only found wheels for `dearpygui` (v2.3.1) with the following Python ABI tags: `cp38`, `cp39`, `cp310`, `cp311`, `cp312`, `cp313`, `cp314`
```

So until Dear PyGui release with wheels for your Python version becomes available, use an environment with an older Python version.

### Application tries to connect to remote hosts on startup and sometimes crashes

Sometimes when you are just launching the application, so you didn't even have a chance to execute any queries, you might notice that it tries to reach various remote hosts on the internet, such as `obspm.fr`, `ietf.org` or probably others.

This is because of the [Astropy](https://astropy.org) package, which is an indirect dependency through PyVO, which is a direct dependency of this project. Specifically, it's the hosts listed in [this file](https://github.com/astropy/astropy/blob/main/astropy/utils/iers/iers.py). Looks harmless enough, apparently just updating some astronomical data.

Denying access to these hosts might lead to the application crash, because Astropy doesn't handle such situation properly:

```
AttributeError: module 'IPython.utils.io' has no attribute 'stdout'
```

If you get the application crashing even when access to those is allowed, try to update the Astropy (*and probably also PyVO*) package:

``` sh
$ pip install astropy -U
```

I had this problem with Astropy v4.2, and it was gone after updating to Astropy v5.1. Or perhaps the problem isn't really gone, but the new package version just came with updated data, so for now there is no need for updating.

### Queries might fail with UnicodeDecodeError

If query results from a TAP service contain non-ASCII symbols, then PyVO will raise [an exception](https://github.com/retifrav/tap-adql-sandbox/issues/19). The application won't crash, but you won't get query results either.

### SIMBAD at CDS is unavailable since October 2026

Since late October 2026 (*the first reports are from 28-30 October*) [CDS](https://cds.unistra.fr/) in Strasbourg has been dealing with a cybersecurity incident, and as part of that it took its servers offline, SIMBAD included. As of 2026-11-20 they are still down, and every request to `simbad.cds.unistra.fr` gets a 404 page, so queries fail with:

``` sh
DALServiceError: 404 Client Error: Not Found for url: https://simbad.cds.unistra.fr/simbad/sim-tap/sync
```

SIMBAD hasn't moved anywhere, it is just temporarily unavailable, and in the meantime CDS [suggests](https://cds.unistra.fr/) using its official mirrors:

- [CfA Harvard](https://simbad.cfa.harvard.edu/simbad/), TAP service at `https://simbad.cfa.harvard.edu/simbad/sim-tap` (*contains data ingested up to 2026-10-14*);
- [IDIA](https://simbad.idia.ac.za/) (*South Africa*), TAP service at `https://simbad.idia.ac.za/simbad/sim-tap`.

So the application still tries the main SIMBAD server first every time (*in case it is back*), and if that fails, it falls back to the mirrors, printing a message about that to stdout:

``` sh
[WARNING] [https://simbad.cds.unistra.fr/simbad/sim-tap] is unavailable, falling back to [https://simbad.cfa.harvard.edu/simbad/sim-tap]. DALServiceError: 404 Client Error: Not Found for url: https://simbad.cds.unistra.fr/simbad/sim-tap/sync
[INFO] Got results from the mirror [https://simbad.cfa.harvard.edu/simbad/sim-tap]
```

That applies to:

- queries to the SIMBAD TAP service, but only when the service URL is exactly the one from the SIMBAD examples (*Help → Examples → SIMBAD*), as any other URL is used as it is. To query a particular mirror, put its URL into the service URL field;
- the SIMBAD IDs lookup (*Tools → Lookup IDs in Simbad*), which first tries the server configured in Astroquery (*the CDS one by default*), and then the mirrors that Astroquery knows about. With Astroquery `0.4.11` that is only CfA Harvard, the IDIA mirror comes in its next release. This requires Astroquery `0.4.8` or later, older versions will just fail as before.

### Queries might be blocked with 403 Forbidden

Some services, such as [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/), have [Cloudflare](https://cloudflare.com/) in front of their servers, and Cloudflare's firewall blocks some perfectly valid ADQL queries, because to the firewall they look like an SQL injection attack. Such a query fails with:

``` sh
403 Client Error: Forbidden for url: https://exoplanetarchive.ipac.caltech.edu/TAP/sync
```

The request never reaches the TAP service, so it is neither an error in the query nor in the application. As of 2026-11-22, the firewall blocks a string literal followed by `AND` or `OR` and then an `IS NULL` or `IS NOT NULL` condition, for example:

``` sql
WHERE pl_name = 'Kepler-106 e' AND pl_radj IS NOT NULL
```

Queries with a subquery in `WHERE` were blocked as well, and there are probably other such patterns. Rephrasing the query without changing its meaning usually gets it through, for example by reordering the conditions:

``` sql
WHERE pl_radj IS NOT NULL AND pl_name = 'Kepler-106 e'
```

or by writing `AND NOT pl_radj IS NULL` instead of `AND pl_radj IS NOT NULL`.

The application tries to recognize Cloudflare's block page and adds an explanation to the error message, along with the Cloudflare Ray ID of the blocked request. If rephrasing doesn't help, you can try reporting this to the service and refer to that Ray ID in your report.

### NASA Exoplanet Archive no longer accepts WITH and subqueries in FROM

One of the queries examples for NASA used to be the following query:

``` sql
SELECT * FROM
(WITH latestEntries AS
    (SELECT hostname, pl_name, pl_radj,
    ROW_NUMBER() OVER(
        PARTITION BY pl_name ORDER BY CASE WHEN pl_radj IS NULL THEN 1 ELSE 0 END, pl_pubdate DESC
    ) AS rank
    FROM ps WHERE hostname = 'Kepler-106')
SELECT hostname, pl_name, pl_radj FROM latestEntries WHERE rank = 1 ORDER BY pl_name)
```

and it worked fine since the time it was added in January 2022 and for some years after that. But as of 2026-11-22, it fails with:

``` sh
Table 'latestentries' is not available for querying. Use TAP_SCHEMA.tables to see available tables.
```

Apparently, it is not the database that rejects it. The database behind the archive's TAP service is Oracle, and it was Oracle back then too (*the archive's [TAP documentation](https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html) has been naming it at least since November 2021*). It still supports everything this query uses: the `ROW_NUMBER() OVER(…)` part, run on its own, works fine. What rejects the query is the TAP service itself. Before passing a query to the database, it checks every table name in the query against `TAP_SCHEMA.tables`, and that check now seems to be checking `latestEntries` too, which is the name of a common table expression (*CTE*) and not an actual table, and it fails as an unknown table. A subquery in `FROM` fails the same way (*`Table '(select' is not available for querying`*), so the query can't be rewritten with one of those either.

Without `WITH` and subqueries, the same result can be had with a self-join, and that is what the example is now:

``` sql
SELECT a.hostname, a.pl_name, a.pl_radj
FROM ps a
JOIN ps b ON b.pl_name = a.pl_name
WHERE a.pl_radj IS NOT NULL AND b.pl_radj IS NOT NULL
AND a.hostname = 'Kepler-106'
GROUP BY a.hostname, a.pl_name, a.pl_radj, a.pl_pubdate
HAVING a.pl_pubdate = MAX(b.pl_pubdate)
ORDER BY a.pl_name
```

For Kepler-106 it returns the same rows as the old query did. In other cases the results might differ: a planet with no `pl_radj` value at all is left out instead of being shown with an empty value, and if two different values share the latest publication date, both of them are returned.

A few more things in this query got a bit of a special treatment too:

- the tables are aliased as `ps a`, not `ps AS a`. That is valid ADQL, but the service passes it to Oracle as it is, and Oracle fails with `ORA-00933: SQL command not properly ended`;
- the condition with the string literal comes last, because otherwise their [firewall](#queries-might-be-blocked-with-403-forbidden) blocks the query;
- the `ON` clause has a single condition. With more conditions joined by `AND` in it, the service takes some of them for table names, the same way as with `latestEntries`.

## 3rd-party

### Dependencies

- Python `3.12` or later
- [Dear PyGui](https://pypi.org/project/dearpygui/) - application window and UI controls
- [PyVO](https://pypi.org/project/pyvo/) - handling TAP ADQL requests
- [Astroquery](https://pypi.org/project/astroquery/) - looking up IDs in Simbad
- [pandas](https://pypi.org/project/pandas/) - processing results and saving to pickle
- [tabulate](https://pypi.org/project/tabulate/) - printing results to stdout (*with `--debug`*)
- transitive (*dependencies of dependencies*):
    + [NumPy](https://pypi.org/project/numpy/) comes through Astroquery(?) and has certain incompatibilities with various versions of Astroquery and pandas, but they all should work fine together if you (re)install the latest versions of all of those

### Resources

- [JetBrains Mono](https://www.jetbrains.com/lp/mono/) font
- [an icon](https://github.com/retifrav/tap-adql-sandbox/tree/master/src/tap_adql_sandbox/icons) of unknown origin

## Donation

You can support this project via [GitHub Sponsors](https://github.com/sponsors/retifrav) or by donating cryptocurrency to either of the following wallets (*[signed variant](https://decovar.dev/donation.txt)*):

- XLM: `GDYB2QGJYWT6VPT7O7INWIGRGJF5ZEAQ7Y73S4T47IOP2QQ554NPN3ZM`
- BTC: `bc1q2kfqwm2kwyw37ay2g4tnguasvp6j4hsmtrgjte`
