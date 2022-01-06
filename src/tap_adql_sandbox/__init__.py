import pathlib

applicationPath = pathlib.Path(__file__).parent.resolve()
settingsFile = str(applicationPath / "settings.ini")
