# 3rd-party dependencies
#
from pyvo.utils import http as pyvoHttp
from requests import Session

# own stuff
#
from .version import __version__

# the User-Agent of every request that the application makes: its own token first,
# then PyVO's ones, as the IVOA Note "Operational Identification of Software Components"
# recommends. PyVO's `create_session()` reads this global on every call, so PyVO's own
# default sessions carry it too. It has to be read through the module after the call,
# because `from pyvo.utils.http import USER_AGENT` would keep PyVO's default
pyvoHttp.setup_user_agent(primary_component=f"tap-adql-sandbox/{__version__}")
userAgent: str = pyvoHttp.USER_AGENT


def addUserAgent(session: Session) -> Session:
    """
    Sets the application's User-Agent on the `session`, replacing whatever
    it had (astroquery's own session has astroquery's User-Agent).
    """
    session.headers["User-Agent"] = userAgent
    return session
