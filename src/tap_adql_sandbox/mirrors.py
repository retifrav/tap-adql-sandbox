# standard libraries
#
import logging
from collections.abc import Callable, Generator
from contextlib import contextmanager
from contextvars import ContextVar

# 3rd-party dependencies
#
from pyvo.dal import DALProtocolError
from requests import Session
from requests.adapters import HTTPAdapter

# own stuff
#
from . import config
from .examples import tapServices

logger: logging.Logger = logging.getLogger(__name__)

# connect timeout (in seconds) of the current `tryMirrors()` attempt,
# which `ConnectTimeoutAdapter` applies, `None` meaning no timeout
attemptConnectTimeout: ContextVar[float | None] = ContextVar(
    "attemptConnectTimeout",
    default=None
)

# errors meaning that a server is down or unreachable, so a mirror might still answer.
# PyVO raises `DALProtocolError` subclasses for those: HTTP errors (such as a 404 page)
# become `DALServiceError`, and a connection error or a timeout in a query becomes `DALFormatError`.
# `OSError` is for a connection error or a timeout from `requests` that PyVO lets through
# as it is. Errors in the query itself (`DALQueryError`) would be the same on every mirror,
# so those are not retried
unavailableErrors: tuple[type[Exception], ...] = (DALProtocolError, OSError)


class ConnectTimeoutAdapter(HTTPAdapter):
    """
    Gives the requests that have no timeout of their own (and neither PyVO nor astroquery sets one)
    the connect timeout of the current `tryMirrors()` attempt, if it has one. Waiting for the response
    stays unlimited.
    """
    def send(self, request, **kwargs):
        connectTimeout: float | None = attemptConnectTimeout.get()
        if kwargs.get("timeout") is None and connectTimeout is not None:
            # a (connect, read) pair, `None` being no limit
            kwargs["timeout"] = (connectTimeout, None)
        return super().send(request, **kwargs)


def addConnectTimeout(session: Session) -> Session:
    """
    Mounts `ConnectTimeoutAdapter` on the `session`, so the connect timeout from `tryMirrors()`
    applies to its requests. Outside of the attempts that have that timeout it changes nothing.
    """
    adapter: ConnectTimeoutAdapter = ConnectTimeoutAdapter()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


@contextmanager
def connectTimeout(seconds: float) -> Generator[None]:
    token = attemptConnectTimeout.set(seconds)
    try:
        yield
    finally:
        attemptConnectTimeout.reset(token)


def tryMirrors[T](servers: list[str], attempt: Callable[[str], T]) -> T:
    """
    Calls `attempt` with each of the `servers` in turn until one of them is available.
    The first one is the main server, so it is tried first on every call, in case
    it is back. If there are mirrors after it, it gets only a short time to accept
    the connection (with sessions from `addConnectTimeout()`), the mirrors have
    no such limit. Errors from the last one propagate as they are, so with no mirrors
    this is the same as a plain call.
    """
    for i, server in enumerate(servers[:-1]):
        logger.debug(f"Trying [{server}]")
        try:
            if i == 0:
                with connectTimeout(config.mainServerConnectTimeout):
                    result: T = attempt(server)
            else:
                result = attempt(server)
        except unavailableErrors as ex:
            logger.warning(
                f"[{server}] is unavailable, "
                f"falling back to [{servers[i + 1]}]. "
                f"{type(ex).__name__}: {ex}"
            )
            continue
        if i > 0:
            logger.info(f"Got results from the mirror [{server}]")
        return result
    logger.debug(f"Trying [{servers[-1]}]")
    result = attempt(servers[-1])
    if len(servers) > 1:
        logger.info(f"Got results from the mirror [{servers[-1]}]")
    return result


def getTapServiceMirrors(serviceURL: str) -> list[str]:
    """
    Returns mirrors of a TAP service from the examples, if `serviceURL` is the URL
    of such a service, so a URL entered by the user is never replaced with some other one.
    """
    for ts in tapServices.values():
        if ts["url"].rstrip("/") == serviceURL.rstrip("/"):
            return ts.get("mirrors", [])
    return []
