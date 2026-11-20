# standard libraries
#
import logging
from collections.abc import Callable

# 3rd-party dependencies
#
from pyvo.dal import DALProtocolError

# own stuff
#
from .examples import tapServices

logger: logging.Logger = logging.getLogger(__name__)

# errors meaning that a server is down or unreachable, so a mirror might still answer.
# PyVO raises `DALProtocolError` subclasses for those: HTTP errors (such as a 404 page)
# become `DALServiceError`, and a connection error or a timeout in a query becomes `DALFormatError`.
# `OSError` is for a connection error or a timeout from `requests` that PyVO lets through
# as it is. Errors in the query itself (`DALQueryError`) would be the same on every mirror,
# so those are not retried
unavailableErrors: tuple[type[Exception], ...] = (DALProtocolError, OSError)


def tryMirrors[T](servers: list[str], attempt: Callable[[str], T]) -> T:
    """
    Calls `attempt` with each of the `servers` in turn until one of them is available.
    The first one is the main server, so it is tried first on every call, in case
    it is back. Errors from the last one propagate as they are, so with no mirrors
    this is the same as a plain call.
    """
    for i, server in enumerate(servers[:-1]):
        logger.debug(f"Trying [{server}]")
        try:
            result: T = attempt(server)
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
