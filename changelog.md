# Changelog

<!-- MarkdownTOC -->

- [0.7.2](#072)
- [0.7.1](#071)
- [0.7.0](#070)
- [0.6.0](#060)
- [0.5.1](#051)
- [0.5.0](#050)
- [0.4.0](#040)
- [0.3.0](#030)
- [0.2.0](#020)
- [0.1.0](#010)

<!-- /MarkdownTOC -->

## 0.7.2

Released on `2022-11-20`.

- better loading indicator
- smaller query text area
- clickable link with repository URL
- some more development menu items
- some small bugfixes

## 0.7.1

Released on `2022-10-09`.

- queries examples for [Gaia Archive](https://gea.esac.esa.int/archive/) database
- tables descriptions in example queries, more precise querying exactly for tables
- more compact About window contents
- lowered Python requirement to v3.6 (*should be fine*)

## 0.7.0

Released on `2022-02-19`.

- not rendering results table for more than 64 columns (*Dear PyGui limitation*), showing warning instead ([#14](https://github.com/retifrav/tap-adql-sandbox/issues/14))
- added horizontal scroll for results table when it has too many columns to fit
- fixed incorrect table cells tagging scheme ([#15](https://github.com/retifrav/tap-adql-sandbox/issues/15))
- artificial enumerating column in results table can be disabled with `--no-enum-column` ([#17](https://github.com/retifrav/tap-adql-sandbox/issues/17))
- added more queries examples ([#16](https://github.com/retifrav/tap-adql-sandbox/issues/16))

## 0.6.0

Released on `2022-01-20`.

- copying results table cell value on right-click
- actually useful pre-filled service URL and query text on launch
- added missing shortcut keyboard codes for Windows and GNU/Linux
- loading indicator gets hidden only when the results table is ready
- clipping results table to improve application performance

## 0.5.1

Released on `2022-01-16`.

- fixed overwriting default floatfmt value even if `--tbl-flt-prcs` was not provided

## 0.5.0

Released on `2022-01-16`.

- `Control/Command + R` keyboard shortcut and menu item for executing query
- workaround for segmentation fault on exit after opening About window
- CLI option for setting floatfmt for tabulate
- support for Cyrillic symbols
- more query examples

## 0.4.0

Released on `2022-01-04`.

- added functionality for saving results to a pickle file
- fixed an error with deleting already deleted results table widget

## 0.3.0

Released on `2022-01-03`.

- query results are output into a table widget

## 0.2.0

Released on `2022-01-02`.

- actually executing queries, results are printed to stdout/console
- some basic user input validation
- showing errors in GUI
- pre-filled examples of queries

## 0.1.0

Released on `2022-01-01`.

- first version, though without actual querying functionality
