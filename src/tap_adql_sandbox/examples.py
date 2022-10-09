examplesList = {
    # ---
    # PADC
    # ---
    "padc-tables":
    {
        "description": "All available tables",
        "serviceURL": "http://voparis-tap-planeto.obspm.fr/tap",
        "queryText": "".join((
            "SELECT table_name, description\n"
            "FROM tap_schema.tables\n"
            "WHERE table_type = 'table'\n"
            "ORDER BY table_name"
        ))
    },
    "padc-columns":
    {
        "description": "All available columns in the table",
        "serviceURL": "http://voparis-tap-planeto.obspm.fr/tap",
        "queryText": "".join((
            "SELECT column_name, datatype, description\n",
            "FROM tap_schema.columns\n",
            "WHERE table_name = 'exoplanet.epn_core'\n",
            "ORDER BY column_name"
        ))
    },
    "padc-stars-count":
    {
        "description": "Total number of stars",
        "serviceURL": "http://voparis-tap-planeto.obspm.fr/tap",
        "queryText": "".join((
            "SELECT COUNT(DISTINCT star_name) AS stars\n",
            "FROM exoplanet.epn_core"
        ))
    },
    "padc-planets-count":
    {
        "description": "Total number of planets",
        "serviceURL": "http://voparis-tap-planeto.obspm.fr/tap",
        "queryText": "".join((
            "SELECT COUNT(DISTINCT granule_uid) AS planets\n",
            "FROM exoplanet.epn_core"
        ))
    },
    "padc-systems-with-minumum-planets":
    {
        "description": "Systems with minimum 6 planets",
        "serviceURL": "http://voparis-tap-planeto.obspm.fr/tap",
        "queryText": "".join((
            "SELECT star_name, COUNT(*) as planets\n",
            "FROM exoplanet.epn_core\n",
            "WHERE star_name IS NOT NULL\n",
            "GROUP BY star_name\n",
            "HAVING COUNT(*) > 5\n",
            "ORDER BY planets DESC"
        ))
    },
    "padc-system-planets":
    {
        "description": "Planets in the system",
        "serviceURL": "http://voparis-tap-planeto.obspm.fr/tap",
        "queryText": "".join((
            "SELECT star_name, granule_uid, mass, radius, period, semi_major_axis\n",
            "FROM exoplanet.epn_core\n",
            "WHERE star_name = 'Kepler-107'\n",
            "ORDER BY granule_uid"
        ))
    },
    "padc-system-planets-with-not-null":
    {
        "description": "Planets with known parameters",
        "serviceURL": "http://voparis-tap-planeto.obspm.fr/tap",
        "queryText": "".join((
            "SELECT star_name, granule_uid, mass, radius\n",
            "FROM exoplanet.epn_core\n",
            "WHERE star_name = 'HD 219134' AND mass IS NOT NULL AND radius IS NOT NULL\n",
            "ORDER BY granule_uid"
        ))
    },
    "padc-star-highest-metallicity":
    {
        "description": "Star with highest metallicity",
        "serviceURL": "http://voparis-tap-planeto.obspm.fr/tap",
        "queryText": "".join((
            "SELECT TOP 1 star_name, star_metallicity\n",
            "FROM exoplanet.epn_core\n",
            "WHERE star_metallicity IS NOT NULL\n",
            "ORDER BY star_metallicity DESC"
        ))
    },
    # ---
    # NASA
    # ---
    "nasa-tables":
    {
        "description": "All available tables",
        "serviceURL": "https://exoplanetarchive.ipac.caltech.edu/TAP",
        "queryText": "".join((
            "SELECT table_name, description\n"
            "FROM tap_schema.tables\n"
            "WHERE table_type = 'table'\n"
            "ORDER BY table_name"
        ))
    },
    "nasa-columns":
    {
        "description": "All available columns in the table",
        "serviceURL": "https://exoplanetarchive.ipac.caltech.edu/TAP",
        "queryText": "".join((
            "SELECT column_name, datatype, description\n",
            "FROM tap_schema.columns\n",
            "WHERE table_name = 'ps'\n",
            "ORDER BY column_name"
        ))
    },
    "nasa-stars-count":
    {
        "description": "Total number of stars",
        "serviceURL": "https://exoplanetarchive.ipac.caltech.edu/TAP",
        "queryText": "".join((
            "SELECT COUNT(DISTINCT hostname) AS stars\n",
            "FROM ps"
        ))
    },
    "nasa-planets-count":
    {
        "description": "Total number of planets",
        "serviceURL": "https://exoplanetarchive.ipac.caltech.edu/TAP",
        "queryText": "".join((
            "SELECT COUNT(DISTINCT pl_name) AS planets\n",
            "FROM ps"
        ))
    },
    "nasa-planet-parameter":
    {
        "description": "Planet parameter by publications",
        "serviceURL": "https://exoplanetarchive.ipac.caltech.edu/TAP",
        "queryText": "".join((
            "SELECT hostname, pl_name, pl_radj, pl_pubdate\n",
            "FROM ps\n",
            "WHERE pl_name = 'Kepler-106 e' AND pl_radj IS NOT NULL\n"
            "ORDER BY pl_pubdate DESC"
        ))
    },
    "nasa-planet-parameter-partition":
    {
        "description": "Most recent value of a planets parameter",
        "serviceURL": "https://exoplanetarchive.ipac.caltech.edu/TAP",
        "queryText": "".join((
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
    },
    # ---
    # Gaia
    # ---
    "gaia-tables":
    {
        "description": "All available tables",
        "serviceURL": "https://gea.esac.esa.int/tap-server/tap",
        "queryText": "".join((
            "SELECT table_name\n"
            "FROM tap_schema.tables\n"
            "WHERE table_type = 'table'\n"
            "ORDER BY table_name"
        ))
    },
    "gaia-columns":
    {
        "description": "All available columns in the table",
        "serviceURL": "https://gea.esac.esa.int/tap-server/tap",
        "queryText": "".join((
            "SELECT column_name, datatype, description\n",
            "FROM tap_schema.columns\n",
            "WHERE table_name = 'gaiadr3.gaia_source'\n",
            "ORDER BY column_name"
        ))
    },
    "gaia-star-parameters":
    {
        "description": "Star parameters",
        "serviceURL": "https://gea.esac.esa.int/tap-server/tap",
        "queryText": "".join((
            "SELECT source_id, solution_id, radius_flame_spec, mass_flame_spec\n",
            "FROM gaiadr3.astrophysical_parameters_supp\n",
            "WHERE source_id = 3145754895088191744"
        ))
    }
}
