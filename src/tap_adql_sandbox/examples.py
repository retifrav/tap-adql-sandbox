import typing

tapServices: typing.Dict[str, typing.Dict] = {
    "padc":
    {
        "name": "PADC",
        "url": "http://voparis-tap-planeto.obspm.fr/tap",
        "examples":
        [
            {
                "description": "All available tables",
                "query": "".join((
                    "SELECT table_name, description\n"
                    "FROM tap_schema.tables\n"
                    "WHERE table_type = 'table'\n"
                    "ORDER BY table_name"
                ))
            },
            {
                "description": "All available columns in the table",
                "query": "".join((
                    "SELECT column_name, datatype, description\n",
                    "FROM tap_schema.columns\n",
                    "WHERE table_name = 'exoplanet.epn_core'\n",
                    "ORDER BY column_name"
                ))
            },
            {
                "description": "Total number of stars",
                "query": "".join((
                    "SELECT COUNT(DISTINCT star_name) AS stars\n",
                    "FROM exoplanet.epn_core"
                ))
            },
            {
                "description": "Total number of planets",
                "query": "".join((
                    "SELECT COUNT(DISTINCT granule_uid) AS planets\n",
                    "FROM exoplanet.epn_core"
                ))
            },
            {
                "description": "Systems with minimum 6 planets",
                "query": "".join((
                    "SELECT star_name, COUNT(*) as planets\n",
                    "FROM exoplanet.epn_core\n",
                    "WHERE star_name IS NOT NULL\n",
                    "GROUP BY star_name\n",
                    "HAVING COUNT(*) > 5\n",
                    "ORDER BY planets DESC"
                ))
            },
            {
                "description": "Planets in the system",
                "query": "".join((
                    "SELECT star_name, granule_uid, mass, radius, period, semi_major_axis\n",
                    "FROM exoplanet.epn_core\n",
                    "WHERE star_name = 'Kepler-107'\n",
                    "ORDER BY granule_uid"
                ))
            },
            {
                "description": "Planets with known parameters",
                "query": "".join((
                    "SELECT star_name, granule_uid, mass, radius\n",
                    "FROM exoplanet.epn_core\n",
                    "WHERE star_name = 'HD 219134' AND mass IS NOT NULL AND radius IS NOT NULL\n",
                    "ORDER BY granule_uid"
                ))
            },
            {
                "description": "Star with highest metallicity",
                "query": "".join((
                    "SELECT TOP 1 star_name, star_metallicity\n",
                    "FROM exoplanet.epn_core\n",
                    "WHERE star_metallicity IS NOT NULL\n",
                    "ORDER BY star_metallicity DESC"
                ))
            }
        ]
    },
    "nasa":
    {
        "name": "NASA",
        "url": "https://exoplanetarchive.ipac.caltech.edu/TAP",
        "examples":
        [
            {
                "description": "All available tables",
                "query": "".join((
                    "SELECT table_name, description\n"
                    "FROM tap_schema.tables\n"
                    "WHERE table_type = 'table'\n"
                    "ORDER BY table_name"
                ))
            },
            {
                "description": "All available columns in the table",
                "query": "".join((
                    "SELECT column_name, datatype, description\n",
                    "FROM tap_schema.columns\n",
                    "WHERE table_name = 'ps'\n",
                    "ORDER BY column_name"
                ))
            },
            {
                "description": "Total number of stars",
                "query": "".join((
                    "SELECT COUNT(DISTINCT hostname) AS stars\n",
                    "FROM ps"
                ))
            },
            {
                "description": "Total number of planets",
                "query": "".join((
                    "SELECT COUNT(DISTINCT pl_name) AS planets\n",
                    "FROM ps"
                ))
            },
            {
                "description": "Planet parameter by publications",
                "query": "".join((
                    "SELECT hostname, pl_name, pl_radj, pl_pubdate\n",
                    "FROM ps\n",
                    "WHERE pl_name = 'Kepler-106 e' AND pl_radj IS NOT NULL\n"
                    "ORDER BY pl_pubdate DESC"
                ))
            },
            {
                "description": "Most recent value of a planets parameter",
                "query": "".join((
                    "SELECT * FROM\n",
                    "(WITH latestEntries AS\n",
                    "\t(SELECT hostname, pl_name, pl_radj,\n",
                    "\tROW_NUMBER() OVER(\n\t\tPARTITION BY pl_name ORDER BY CASE ",
                    "WHEN pl_radj IS NULL THEN 1 ELSE 0 END, pl_pubdate DESC\n\t) ",
                    "AS rank\n"
                    "\tFROM ps WHERE hostname = 'Kepler-106')\n",
                    "SELECT hostname, pl_name, pl_radj FROM latestEntries ",
                    "WHERE rank = 1 ORDER BY pl_name)"
                ))
            }
        ]
    },
    "gaia":
    {
        "name": "Gaia",
        "url": "https://gea.esac.esa.int/tap-server/tap",
        "examples":
        [
            {
                "description": "All available tables",
                "query": "".join((
                    "SELECT table_name\n"
                    "FROM tap_schema.tables\n"
                    "WHERE table_type = 'table'\n"
                    "ORDER BY table_name"
                ))
            },
            {
                "description": "All available columns in the table",
                "query": "".join((
                    "SELECT column_name, datatype, description\n",
                    "FROM tap_schema.columns\n",
                    "WHERE table_name = 'gaiadr3.gaia_source'\n",
                    "ORDER BY column_name"
                ))
            },
            {
                "description": "Star parameters",
                "query": "".join((
                    "SELECT source_id, solution_id, mass_flame, radius_flame\n",
                    "FROM gaiadr3.astrophysical_parameters\n",
                    "WHERE source_id = 3145754895088191744"
                ))
            }
        ]
    },
    "simbad":
    {
        "name": "SIMBAD",
        "url": "http://simbad.cds.unistra.fr/simbad/sim-tap/sync",
        "examples":
        [
            {
                "description": "All available tables",
                "query": "".join((
                    "SELECT table_name\n"
                    "FROM tap_schema.tables\n"
                    "WHERE table_type = 'table'\n"
                    "ORDER BY table_name"
                ))
            },
            {
                "description": "All available columns in the table",
                "query": "".join((
                    "SELECT column_name, datatype, description\n",
                    "FROM tap_schema.columns\n",
                    "WHERE table_name = 'basic'\n",
                    "ORDER BY column_name"
                ))
            },
            {
                "description": "Object ID by name",
                "query": "".join((
                    "SELECT oid\n",
                    "FROM basic\n",
                    "WHERE main_id = 'CD-29 2360'"
                ))
            },
            {
                "description": "Star parameter by publications",
                "query": "".join((
                    "SELECT v.period, v.bibcode\n",
                    "FROM mesVar AS v\n",
                    "JOIN basic AS b ON v.oidref = b.oid\n",
                    "WHERE b.main_id = 'CD-29 2360'\n",
                    "ORDER BY bibcode DESC"
                ))
            }
        ]
    }
}
