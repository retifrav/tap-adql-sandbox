examplesList = {
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
    "padc-system-planets":
    {
        "description": "Planets in the system and their parameters",
        "serviceURL": "http://voparis-tap-planeto.obspm.fr/tap",
        "queryText": "".join((
            "SELECT star_name, granule_uid, mass, radius\n",
            "FROM exoplanet.epn_core\n",
            "WHERE star_name = 'Kepler-106'\n",
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
        "description": "Latest planet parameter in the system",
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
            "WHERE rank = 1)"
        ))
    }
}
