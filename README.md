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
- [3rd-party](#3rd-party)
    - [Requirements](#requirements)
    - [Resources](#resources)

<!-- /MarkdownTOC -->

## About

A sandbox application for executing ADQL queries via TAP interface of various data sources, such as astronomical databases. Essentially, it's just a GUI for [PyVO](https://pypi.org/project/pyvo/).

![TAP ADQL sandbox](https://raw.githubusercontent.com/retifrav/tap-adql-sandbox/master/misc/screenshot-main-macos.png "TAP ADQL sandbox")

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

## Running

``` sh
$ tap-adql-sandbox --help
```

## Platforms

Tested on:

- Mac OS:
    + 11.6.2, Intel
- Windows:
    + 10
    + 11
- GNU/Linux:
    + Ubuntu 20.04

## Known problems

- if `SELECT` requests a lot of columns, the results table [might not have](https://github.com/retifrav/tap-adql-sandbox/issues/8) visible contents, or the application [might just crash](https://github.com/retifrav/tap-adql-sandbox/issues/14)

## 3rd-party

### Requirements

- Python 3.6 or later (*though the oldest tested version is 3.7*)
- [Dear PyGui](https://pypi.org/project/dearpygui/) - application window and UI controls
- [PyVO](https://pypi.org/project/pyvo/) - handling TAP ADQL requests
- [pandas](https://pypi.org/project/pandas/) - processing results and saving to pickle
- [tabulate](https://pypi.org/project/tabulate/) - printing results to stdout (*with `--debug`*)

### Resources

- [JetBrains Mono](https://www.jetbrains.com/lp/mono/) font
- [an icon](https://github.com/retifrav/tap-adql-sandbox/tree/master/src/tap_adql_sandbox/icons) of unknown origin
