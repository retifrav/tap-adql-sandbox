from datetime import datetime

__version_info__: tuple[int, int, int] = (0, 8, 2)
__version__: str = ".".join(map(str, __version_info__))

__copyright__: str = (
    f"Copyright (C) 2022-{datetime.now().year} "
    "Declaration of VAR"
)
