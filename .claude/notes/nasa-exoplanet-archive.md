# NASA Exoplanet Archive: Cloudflare WAF and query checks

Evidence behind the NASA example rules and `getFirewallBlockHint` in `CLAUDE.md`. Gathered on 2026-11-22 with curl POSTs to `https://exoplanetarchive.ipac.caltech.edu/TAP/sync` (`REQUEST=doQuery`, `LANG=ADQL`, `QUERY=…`), on the x86_64 container on the Arch host, plus pyvo 1.10.0 for the exception path.

## Cloudflare WAF

- Cloudflare proxies the whole host. Every response carries `server: cloudflare` and `cf-ray`, including a 200 (`content-type: application/xml`) and the service's own 400 VOTable errors.
- A block is HTTP 403 with `content-type: text/html` and the "Attention Required! | Cloudflare" page: "Sorry, you have been blocked … You are unable to access ipac.caltech.edu … submitting a certain word or phrase, a SQL command or malformed data". The page shows the Ray ID, which is the `cf-ray` header.
- PyVO path: `DALQuery.execute_stream` stores `DALServiceError.from_except(HTTPError)` (`code` = 403, `cause` = the `requests.HTTPError`, whose `.response` has the headers). The HTML fails `votableparse`, so `execute_votable` calls `raise_if_error`, which raises that `DALServiceError`. `from_except` replaces the message with `response.text` only for `text/plain`, so the message stays `403 Client Error: Forbidden for url: …/TAP/sync`.
- Bisect, from the bundled "Planet parameter by publications" example (`SELECT hostname, pl_name … FROM ps WHERE …`):

  | `WHERE` | status |
  |---|---|
  | `pl_name = 'Kepler-106 e'` | 200 |
  | `pl_radj IS NOT NULL` | 200 |
  | `pl_name = 'Kepler-106 e' AND pl_radj IS NOT NULL` | 403 |
  | `pl_name = 'Kepler-106 e' AND pl_radj IS NULL` | 403 |
  | `pl_name = 'Kepler-106 e' OR pl_radj IS NOT NULL` | 403 |
  | `(pl_name = 'Kepler-106 e') AND pl_radj IS NOT NULL` | 403 |
  | `pl_name = 'Kepler-106 e' AND hostname IS NOT NULL` | 403 |
  | `pl_radj IS NOT NULL AND pl_name = 'Kepler-106 e'` | 200 |
  | `pl_name = 'Kepler-106 e' AND pl_radj > 0` | 200 |
  | `pl_name = 'Kepler-106 e' AND NOT pl_radj IS NULL` | 200 |
  | `pl_name = 'Kepler-106 e'` + `ORDER BY pl_pubdate DESC` | 200 |

- Two correlated subqueries in `WHERE` were blocked too: `hostname = 'Kepler-106' AND pl_pubdate = (SELECT MAX(pl_pubdate) FROM ps WHERE pl_name = p.pl_name AND pl_radj IS NOT NULL)`, and the same with the subquery first and `AND a.hostname = 'Kepler-106'` last. The second has no literal before `AND`, so the subquery itself, or `) AND … = '…'`, is enough.
- The rules aren't published, so the table only shows what was blocked on that day. About a dozen requests were blocked over the whole session, test runs included. Keep probing that light, in case Cloudflare escalates to blocking the IP, which it didn't do then.

## The archive's own query checks

- `/TAP/capabilities` declares ADQL 2.0 with only the geometry features (POINT, CIRCLE, BOX, POLYGON, CONTAINS). `TAP_SCHEMA.tables` still lists `ps` and `pscomppars`, and `ps` still has `hostname`, `pl_name`, `pl_radj` and `pl_pubdate` (`pl_pubdate` is a string such as `2024-01` or `2017-08-31 00:00`, so `MAX` and `ORDER BY` compare it as text).
- The old "Most recent value of a planets parameter" example (`SELECT * FROM (WITH latestEntries AS (… ROW_NUMBER() OVER(PARTITION BY pl_name …) …) …)`) worked before, according to the user, and now fails with HTTP 400 and a VOTable `QUERY_STATUS=ERROR`, which PyVO raises as `DALQueryError`: `Table 'latestentries' is not available for querying. Use TAP_SCHEMA.tables to see available tables.` The service checks the table names it finds in the query against a whitelist and doesn't know CTE names.
- Rewrites that failed:
  - A derived table, `FROM (SELECT … ROW_NUMBER() OVER(…) AS rank FROM ps WHERE hostname = 'Kepler-106') latestEntries`: 400, `Table '(select' is not available for querying.`
  - A `LEFT JOIN` anti-join with three `AND`ed conditions in `ON` (`FROM ps AS a LEFT JOIN ps AS b ON b.pl_name = a.pl_name AND b.pl_radj IS NOT NULL AND b.pl_pubdate > a.pl_pubdate`): 400, `Table 'b.pl_radj' is not available for querying.` The whitelist parser takes tokens from the `ON` clause for table names.
  - A self-join with `FROM ps AS a JOIN ps AS b`: 400, `ORA-00933: SQL command not properly ended`. The backend is Oracle and gets `AS` before a table alias as it is, which Oracle doesn't accept.
  - The correlated subqueries above: 403 from the WAF.
- What works, and is now the example: `FROM ps a JOIN ps b ON b.pl_name = a.pl_name`, the `IS NOT NULL` conditions in `WHERE` with the literal last, `GROUP BY a.hostname, a.pl_name, a.pl_radj, a.pl_pubdate`, `HAVING a.pl_pubdate = MAX(b.pl_pubdate)`. It returned one row per planet, Kepler-106 b/c/d/e, all from `2024-01`, and e = 0.23383036 matches the top row of "Planet parameter by publications". Unlike the old query, it leaves out a planet with no non-NULL `pl_radj` instead of showing it with NULL, and returns two rows when two different values share the latest date. Kepler-106 has neither case.
- The backend did not change: it is Oracle now (`ORA-00933` above) and was Oracle when the old query worked. `usingTAP.html` says "ADQL and Oracle table and column names are not case-sensitive" today ("Last updated: 24 July 2026") and in Wayback snapshots from 2022-04-17 (page "Last updated: 19 November 2021"), 2023-05-31 and 2024-12-27. The query was added in `55e654f` on 2022-01-02. The user believed the backend had changed, and was told otherwise on 2026-11-22.
- Oracle still runs the old query's inner part: `SELECT …, ROW_NUMBER() OVER(PARTITION BY pl_name ORDER BY CASE WHEN pl_radj IS NULL THEN 1 ELSE 0 END, pl_pubdate DESC) AS rank FROM ps WHERE hostname = 'Kepler-106' ORDER BY pl_name, rank` returns 200, and its rank-1 rows (b 0.07672419, c 0.21295424, d 0.08992789, e 0.23383036, all `2024-01`) are exactly what the self-join returns. So window functions pass through untranslated, and only the service's table-name check stands between the old query and the database. When that check became stricter can't be seen from outside.
- After the change, all six NASA examples returned 200 with rows: 46 tables, 355 columns of `ps`, the two counts, 10 publications of Kepler-106 e and the 4 planets.

## The hint

- `getFirewallBlockHint` was checked through the built wheel. The live blocked query got the hint with a real Ray ID. The live 400 above (`DALQueryError`) got none, and neither did a real 404 from Gaia's Apache. Synthetic `DALServiceError.from_except` errors got no hint for a Cloudflare 403 with `application/xml`, an nginx 403 with HTML, or a Cloudflare 404 with HTML. A Cloudflare 403 with HTML but no `CF-RAY` header got the hint, ending in `Ray ID: unknown`.
- On Xvfb at `--ui-scale 1`, the message is the PyVO line, a blank line, then the hint, wrapped at the window edge by `wrap=0`, in the error theme's red, with the Execute button restored.
