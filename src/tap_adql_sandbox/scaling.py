# standard libraries
#
import ctypes
import logging
import sys

# 3rd-party dependencies
#
from dearpygui import _dearpygui

# own stuff
#
from . import config

logger: logging.Logger = logging.getLogger(__name__)


def getContentScale() -> float:
    """
    Returns the content scale of the primary monitor on GNU/Linux
    and 1 on other platforms.

    Dear PyGui (as of 2.3.1) does nothing about HiDPI on GNU/Linux:
    its window is created in physical pixels and neither fonts nor
    paddings are scaled, so on a 4K display everything is tiny
    (https://github.com/hoffstadt/DearPyGui/issues/1081). It doesn't
    need this on other platforms: on Mac OS it disables the Retina
    framebuffer and lets the system scale the window, and on Windows
    the system scales a process that isn't DPI-aware.

    Dear ImGui's own GLFW example scales its window, style and fonts
    by `glfwGetMonitorContentScale()` of the primary monitor, which
    on X11 (the only platform of the GLFW that Dear PyGui bundles)
    is `Xft.dpi / 96`. Dear PyGui has no function for that, but its
    extension module links GLFW statically and exports its symbols,
    so they are called through `ctypes`. GLFW has to be initialized
    for that, and Dear PyGui does that only in `show_viewport()`,
    so here it is initialized and terminated again before that.
    """
    if not sys.platform.startswith("linux"):
        return 1.0

    try:
        glfw = ctypes.CDLL(_dearpygui.__file__)
        glfw.glfwInit.restype = ctypes.c_int
        glfw.glfwGetPrimaryMonitor.restype = ctypes.c_void_p
        glfw.glfwGetMonitorContentScale.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_float),
            ctypes.POINTER(ctypes.c_float)
        ]
        glfw.glfwGetMonitorContentScale.restype = None
        glfw.glfwTerminate.restype = None
    except (OSError, AttributeError) as ex:
        logger.warning(
            "Couldn't get GLFW functions from Dear PyGui, "
            f"so the UI won't be scaled for HiDPI. {ex}"
        )
        return 1.0

    # fails when there is no display, but then Dear PyGui will fail too
    if not glfw.glfwInit():
        logger.debug("Couldn't initialize GLFW to get the content scale")
        return 1.0
    xScale = ctypes.c_float(1.0)
    yScale = ctypes.c_float(1.0)
    try:
        monitor = glfw.glfwGetPrimaryMonitor()
        if monitor:
            glfw.glfwGetMonitorContentScale(
                monitor,
                ctypes.byref(xScale),
                ctypes.byref(yScale)
            )
    finally:
        glfw.glfwTerminate()

    scale: float = xScale.value
    logger.debug(f"Content scale of the primary monitor: {scale}")
    # a bogus `Xft.dpi` (such as 0) gives a bogus scale
    if not config.uiScaleMin <= scale <= config.uiScaleMax:
        logger.warning(
            f"Content scale {scale} is out of the supported range "
            f"({config.uiScaleMin} to {config.uiScaleMax}), "
            "so the UI won't be scaled. Use --ui-scale to set it"
        )
        return 1.0
    return scale


def scaled(size: float) -> int:
    """
    Converts a size from the pixels the UI is designed in (which is what
    the user gets on Mac OS) to physical pixels. Every size in pixels
    given to Dear PyGui has to pass through it.
    """
    return round(size * config.uiScale)
