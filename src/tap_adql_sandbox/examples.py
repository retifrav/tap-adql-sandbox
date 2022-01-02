examplesList = {
    "exoplanet.eu":
    {
        "serviceURL": "http://voparis-tap-planeto.obspm.fr/tap",
        "queryText": "".join((
            "SELECT star_name, granule_uid, mass\n",
            "FROM exoplanet.epn_core\n",
            "WHERE star_name = 'Kepler-106'"
        ))
    },
    "NASA":
    {
        "serviceURL": "https://exoplanetarchive.ipac.caltech.edu/TAP",
        "queryText": "".join((
            "SELECT * FROM\n",
            "(WITH latestEntries AS\n",
            "\t(SELECT hostname, pl_name, pl_massj,\n",
            "\tROW_NUMBER() OVER(\n\t\tPARTITION BY pl_name ORDER BY CASE ",
            "WHEN pl_massj IS NULL THEN 1 ELSE 0 END, pl_pubdate DESC\n\t) ",
            "AS rank\n"
            "\tFROM ps WHERE hostname = 'Kepler-106')\n",
            "SELECT hostname, pl_name, pl_massj FROM latestEntries ",
            "WHERE rank = 1)"
        ))
    }
}
