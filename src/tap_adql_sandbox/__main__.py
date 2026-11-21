# standard libraries
#
import argparse
import logging
import pathlib
import sys
import traceback
import typing
import webbrowser
from time import sleep

# 3rd-party dependencies
#
import dearpygui.dearpygui as dpg
import pandas
import pyvo
from dearpygui.demo import show_demo
from tabulate import tabulate

# own stuff
#
from . import applicationPath, config, settingsFile
from .examples import tapServices
from .mirrors import getTapServiceMirrors, tryMirrors
from .scaling import getContentScale, scaled
from .simbad import showSimbadIDsWindow, simbadWindow
from .theme import (
    getCellDefaultTheme,
    getCellHighlightedTheme,
    getCopyableTheme,
    getErrorTheme,
    getGlobalFont,
    getGlobalTheme,
    getHyperlinkTheme,
    getInlineTheme,
    getWindowTheme,
    styleFramePadding,
    stylePrimaryColor,
    stylePrimaryColorActive,
)
from .version import __copyright__, __version__

logger: logging.Logger = logging.getLogger(__name__)

mainWindowID: str = "main-window"
queryTextID: str = "query-text"
serviceUrlID: str = "service-url"

repositoryURL: str = "https://github.com/retifrav/tap-adql-sandbox"

# the same as in the Donation section of README.md
sponsorsURL: str = "https://github.com/sponsors/retifrav"
donationSignedURL: str = "https://decovar.dev/donation.txt"
donationWallets: dict[str, str] = {
    "XLM": "GDYB2QGJYWT6VPT7O7INWIGRGJF5ZEAQ7Y73S4T47IOP2QQ554NPN3ZM",
    "BTC": "bc1q2kfqwm2kwyw37ay2g4tnguasvp6j4hsmtrgjte"
}

lastQueryResults: pandas.DataFrame = pandas.DataFrame()
executingQuery: bool = False


def add_hyperlink(text: str, address: str):
    b = dpg.add_button(
        label=text,
        callback=lambda: webbrowser.open(address)
    )
    dpg.bind_item_theme(b, getHyperlinkTheme())


def showLoading(isLoading: bool) -> None:
    global executingQuery

    if isLoading:
        dpg.hide_item("btnExecuteQuery")
        dpg.configure_item("menuExecuteQuery", enabled=False)
        dpg.show_item("loadingAnimation")
        executingQuery = True
    else:
        dpg.hide_item("loadingAnimation")
        dpg.show_item("btnExecuteQuery")
        dpg.configure_item("menuExecuteQuery", enabled=True)
        executingQuery = False


def keyPressCallback(sender, app_data) -> None:
    # logger.debug(f"sender: {sender}, app_data: {app_data}")

    # dpg.is_item_focused
    if not dpg.is_item_active(queryTextID) or executingQuery:
        return

    # the handler fires on `R`, so check for the modifier. On Mac OS
    # Dear ImGui reports `Cmd` as `Ctrl`, which makes it `Cmd + R` there
    if dpg.is_key_down(dpg.mvKey_ModCtrl):
        # executingQuery = True
        logger.debug(
            "Triggered executing query "
            "from the keyboard shortcut"
        )
        executeQuery()


def executeQuery() -> None:
    global lastQueryResults

    # clear previously saved results
    lastQueryResults = pandas.DataFrame()

    dpg.hide_item("resultsGroup")
    if dpg.does_item_exist("resultsTable"):
        dpg.delete_item("resultsTable")
    dpg.hide_item("errorMessage")
    dpg.set_value("errorMessage", "")

    dpg.configure_item("menuSaveFile", enabled=False)
    showLoading(True)

    serviceURL: str = dpg.get_value(serviceUrlID).strip()
    queryText: str = dpg.get_value(queryTextID).strip()

    if not serviceURL:
        dpg.set_value("errorMessage", "No service URL provided.")
        dpg.show_item("errorMessage")
        showLoading(False)
        return

    if not queryText:
        dpg.set_value("errorMessage", "Cannot execute an empty query.")
        dpg.show_item("errorMessage")
        showLoading(False)
        return

    logger.debug(f"Query to execute:\n{queryText}")

    results: pyvo.dal.DALResults = {}
    try:
        results = tryMirrors(
            [serviceURL] + getTapServiceMirrors(serviceURL),
            lambda url: pyvo.dal.TAPService(url).search(queryText)
        )
    except Exception as ex:
        logger.debug(f"Query failed: {ex}")
        dpg.set_value("errorMessage", ex)
        dpg.show_item("errorMessage")
        showLoading(False)
        return

    logger.debug(f"Results found: {len(results)}")
    if config.debugMode:
        try:
            # won't look nice with logger.debug(), so it's a print()
            print(
                tabulate(
                    results.to_table(),
                    headers=results.fieldnames,
                    tablefmt="psql",
                    floatfmt=config.tabulateFloatfmtPrecision
                )
            )
        except Exception as ex:
            logger.warning(f"Couldn't print results. {ex}")

    lastQueryResults = results.to_table().to_pandas()
    rowsCount, columnsCount = lastQueryResults.shape
    logger.debug(f"Columns: {columnsCount}, rows: {rowsCount}")
    addEnumerationColumn: bool = (
        not config.noEnumerationColumn and rowsCount > 1
    )
    # https://github.com/retifrav/tap-adql-sandbox/issues/8
    # https://github.com/retifrav/tap-adql-sandbox/issues/14
    if columnsCount + int(addEnumerationColumn) > config.dpgColumnsMax:
        dpg.set_value(
            "errorMessage",
            (
                "You have requested too many columns in your query. "
                f"A table can have maximum {config.dpgColumnsMax} columns, "
                "including the enumeration column (which can be "
                "disabled with --no-enum-column), and so trying "
                "to display results for your query would crash "
                "the application. Remove some columns from your SELECT "
                "statement and try again."
            )
        )
        dpg.show_item("errorMessage")
        showLoading(False)
        return
    try:
        # when there isn't that many columns,
        # squeezed table doesn't look nice
        addHorizontalScroll = (
            dpg.get_item_width(mainWindowID) / columnsCount < scaled(150)
        )
        with dpg.table(
            parent="resultsGroup",
            tag="resultsTable",
            header_row=True,
            resizable=True,
            borders_outerH=True,
            borders_innerV=True,
            borders_innerH=True,
            borders_outerV=True,
            clipper=True,
            # row_background=True,
            # freeze_rows=0,
            # freeze_columns=1,
            # scrollY=True,
            policy=(
                dpg.mvTable_SizingFixedSame
                if addHorizontalScroll
                else dpg.mvTable_SizingStretchProp
            ),
            scrollX=addHorizontalScroll
        ):
            if addEnumerationColumn:
                dpg.add_table_column(label="#")
            for header in lastQueryResults.columns:
                dpg.add_table_column(label=header)
            for index, row in lastQueryResults.iterrows():
                # reveal_type(index)
                index = typing.cast(int, index)
                with dpg.table_row():
                    if addEnumerationColumn:
                        with dpg.table_cell():
                            dpg.add_text(default_value=f"{index+1}")
                    cellIndex: int = 1
                    for cell in row:
                        with dpg.table_cell():
                            cellID = f"cell-{index+1}-{cellIndex}"
                            dpg.add_text(
                                tag=cellID,
                                default_value=cell
                            )
                            dpg.bind_item_handler_registry(
                                cellID,
                                "cell-handler"
                            )
                        cellIndex += 1
    except Exception as ex:
        errorMsg = "Couldn't generate the results table"
        logger.error(f"{errorMsg}. {ex}")
        if config.debugMode:
            traceback.print_exc(file=sys.stderr)
        dpg.set_value(
            "errorMessage",
            f"{errorMsg}. There might be more details in console/stderr."
        )
        dpg.show_item("errorMessage")
        showLoading(False)
        return
    showLoading(False)
    dpg.show_item("resultsGroup")
    dpg.configure_item("menuSaveFile", enabled=True)


def preFillExample(sender, app_data, user_data: tuple[str, str]) -> None:
    dpg.set_value(serviceUrlID, user_data[0])
    dpg.set_value(queryTextID, user_data[1])


def saveResultsToPickle(sender, app_data, user_data) -> None:
    logger.debug(f"app_data: {app_data}")
    # this check might be redundant,
    # as dialog window apparently performs it on its own
    pickleFileDir: pathlib.Path = pathlib.Path(app_data["current_path"])
    if not pickleFileDir.is_dir():
        logger.error(f"The [{pickleFileDir}] directory does not exist")
        return
    pickleFile: pathlib.Path = pickleFileDir / app_data["file_name"]
    try:
        lastQueryResults.to_pickle(pickleFile)
    except Exception as ex:
        logger.error(f"Couldn't save results to [{pickleFile}]: {ex}")
        return


def cellClicked(sender, app_data) -> None:
    # logger.debug(f"sender: {sender}, app_data: {app_data}")

    # mouse right click
    if app_data[0] == 1:
        cellValue = dpg.get_value(app_data[1])
        # logger.debug(f"cellValue: {cellValue}")
        dpg.set_clipboard_text(cellValue)
        dpg.set_value(app_data[1], "[copied]")
        dpg.bind_item_theme(app_data[1], getCellHighlightedTheme())
        sleep(1)
        dpg.bind_item_theme(app_data[1], getCellDefaultTheme())
        dpg.set_value(app_data[1], cellValue)


def walletAddressClicked(
    sender,
    app_data,
    user_data: tuple[str, int | str, int | str]
) -> None:
    address, copyableTheme, copiedTheme = user_data
    dpg.set_clipboard_text(address)
    # padded on the right to the length of the address, so it starts where the address starts,
    # and the button keeps its width (the font is monospaced)
    dpg.configure_item(sender, label="[copied]".ljust(len(address)))
    dpg.bind_item_theme(sender, copiedTheme)
    sleep(1)
    dpg.bind_item_theme(sender, copyableTheme)
    dpg.configure_item(sender, label=address)


def showDPGabout() -> None:
    dpg.hide_item("aboutWindow")
    dpg.show_about()


def main() -> None:
    argParser = argparse.ArgumentParser(
        prog="tap-adql-sandbox",
        description=(
            f"%(prog)s\n{__copyright__}\nA "
            "sandbox application for executing ADQL queries "
            "via TAP interface of various data sources"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False
    )
    argParser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    argParser.add_argument(
        "--debug",
        action='store_true',
        help="enable debug/dev mode (default: %(default)s)"
    )
    argParser.add_argument(
        "--no-enum-column",
        action='store_true',
        help=(
            "add artificial first column "
            "to enumerate results (default: %(default)s)"
        )
    )
    argParser.add_argument(
        "--tbl-flt-prcs",
        metavar=".8f",
        help="floating point precision for tabulate output"
    )
    argParser.add_argument(
        "--ui-scale",
        metavar="FACTOR",
        type=float,
        help=(
            "scale fonts, controls and windows by this factor, "
            f"from {config.uiScaleMin} to {config.uiScaleMax} "
            "(default: Xft.dpi / 96 on GNU/Linux, 1 on other platforms)"
        )
    )
    cliArgs = argParser.parse_args()
    if (
        cliArgs.ui_scale is not None
        and not config.uiScaleMin <= cliArgs.ui_scale <= config.uiScaleMax
    ):
        argParser.error(
            "--ui-scale has to be "
            f"from {config.uiScaleMin} to {config.uiScaleMax}"
        )
    # logger.debug(cliArgs)

    config.debugMode = cliArgs.debug
    config.noEnumerationColumn = cliArgs.no_enum_column
    if cliArgs.tbl_flt_prcs:
        config.tabulateFloatfmtPrecision = cliArgs.tbl_flt_prcs

    loggingLevel: int = logging.INFO
    loggingFormat: str = "[%(levelname)s] %(message)s"
    if config.debugMode:
        loggingLevel = logging.DEBUG
        # 8 is the length of "critical" - the longest log level name
        loggingFormat = "%(asctime)s | %(levelname)-8s | %(message)s"
    # might want to create separate loggers/handlers for errors to go
    # to stderr, otherwise everything goes to stdout
    logging.basicConfig(
        format=loggingFormat,
        level=loggingLevel,
        stream=sys.stdout  # or set stderr here (which is the default)
    )

    # before any UI is created, because every size depends on it
    config.uiScale = (
        cliArgs.ui_scale
        if cliArgs.ui_scale is not None
        else getContentScale()
    )
    logger.debug(f"UI scale: {config.uiScale}")

    dpg.create_context()

    dpg.configure_app(init_file=settingsFile)

    # dpg.set_frame_callback(2, callback=updateGeometry)
    # dpg.set_viewport_resize_callback(callback=updateGeometry)
    dpg.set_exit_callback(callback=lambda: dpg.save_init_file(settingsFile))

    #
    # --- Simbad window
    #
    simbadWindow()

    #
    # --- main window
    #
    with dpg.window(tag=mainWindowID):
        #
        # --- menu
        #
        with dpg.menu_bar():
            with dpg.menu(label="File"):
                dpg.add_menu_item(
                    tag="menuExecuteQuery",
                    label="Execute query",
                    shortcut="Cmd/Ctrl + R",
                    callback=executeQuery
                )
                dpg.add_spacer()
                dpg.add_separator()
                dpg.add_spacer()
                dpg.add_menu_item(
                    tag="menuSaveFile",
                    label="Save results to pickle...",
                    enabled=False,
                    callback=lambda: dpg.show_item("dialogSaveFile")
                )
                dpg.add_spacer()
                dpg.add_separator()
                dpg.add_spacer()
                dpg.add_menu_item(
                    label="Exit",
                    callback=lambda: dpg.stop_dearpygui()
                )

            # with dpg.menu(label="Settings"):
            #     dpg.add_menu_item(
            #         label="Setting 1",
            #         callback=lambda: print("ololo"),
            #         check=True
            #     )
            #     dpg.add_menu_item(
            #         label="Setting 2",
            #         callback=lambda: print("ololo")
            #     )

            with dpg.menu(label="Tools"):
                dpg.add_menu_item(
                    tag="menu_getSimbadIDs",
                    label="Lookup IDs in Simbad",
                    callback=showSimbadIDsWindow
                )

            if config.debugMode:
                with dpg.menu(label="Dev"):
                    dpg.add_menu_item(
                        label="Performance metrics",
                        callback=lambda: dpg.show_metrics()
                    )
                    dpg.add_menu_item(
                        label="Items registry",
                        callback=lambda: dpg.show_item_registry()
                    )
                    dpg.add_menu_item(
                        label="Styling",
                        callback=lambda: dpg.show_style_editor()
                    )
                    dpg.add_spacer()
                    dpg.add_separator()
                    dpg.add_spacer()
                    dpg.add_menu_item(
                        label="Documentation",
                        callback=lambda: dpg.show_documentation()
                    )
                    dpg.add_spacer()
                    dpg.add_separator()
                    dpg.add_spacer()
                    dpg.add_menu_item(
                        label="Dear PyGui demo",
                        callback=lambda: show_demo()
                    )
                    dpg.add_menu_item(
                        label="Dear ImGui demo",
                        callback=lambda: dpg.show_imgui_demo()
                    )

            with dpg.menu(label="Help"):
                with dpg.menu(label="Examples"):
                    for ts in tapServices:
                        with dpg.menu(label=tapServices[ts]["name"]):
                            for e in tapServices[ts]["examples"]:
                                dpg.add_menu_item(
                                    label=e["description"],
                                    user_data=(
                                        tapServices[ts]["url"],
                                        e["query"]
                                    ),
                                    callback=preFillExample
                                )
                dpg.add_spacer()
                dpg.add_separator()
                dpg.add_spacer()
                dpg.add_menu_item(
                    label="Donation",
                    callback=lambda: dpg.show_item("donationWindow")
                )
                dpg.add_menu_item(
                    label="About",
                    callback=lambda: dpg.show_item("aboutWindow")
                )

        #
        # -- contents
        #
        dpg.add_input_text(
            tag=serviceUrlID,
            hint="TAP service",
            width=-1
        )
        dpg.add_input_text(
            tag=queryTextID,
            # FIXME never shows, because Dear PyGui ignores hints
            # in multiline inputs (it clears them before drawing)
            # https://github.com/hoffstadt/DearPyGui/issues/1519
            hint="ADQL query",
            default_value=(
                "SELECT TOP 11 *\n"
                "FROM some_table\n"
                "WHERE some_thing = 1"
            ),
            width=-1,
            height=scaled(300),
            multiline=True,
            tab_input=True
        )
        dpg.add_button(
            tag="btnExecuteQuery",
            label="Execute query",
            callback=executeQuery
        )
        dpg.add_loading_indicator(
            tag="loadingAnimation",
            style=1,
            radius=2.0,
            # speed=2,
            indent=scaled(7),
            color=stylePrimaryColorActive,
            secondary_color=stylePrimaryColor,
            show=False
        )

        dpg.add_spacer()

        dpg.add_text(
            tag="errorMessage",
            default_value="Error",
            wrap=0,  # 0 wraps the text at the window edge
            show=False
        )

        with dpg.group(tag="resultsGroup", show=False):
            dpg.add_text(default_value="Query results:")
            with dpg.table(tag="resultsTable"):
                dpg.add_table_column(label="Results")

    #
    # --- save file dialog
    #
    with dpg.file_dialog(
        tag="dialogSaveFile",
        directory_selector=False,
        width=scaled(800),
        height=scaled(600),
        modal=True,
        show=False,
        callback=saveResultsToPickle
    ):
        dpg.add_file_extension(".pkl", color=(30, 225, 0))

    #
    # --- error dialog
    #
    # with dpg.window(
    #     tag="errorDialog",
    #     label="Error",
    #     modal=True,
    #     show=False,
    #     width=300
    # ):
    #     dpg.add_text(
    #         tag="errorDialogText",
    #         default_value="Unknown error"
    #     )
    #     dpg.add_button(
    #         label="Close",
    #         callback=lambda: dpg.hide_item("errorDialog")
    #     )
    #     dpg.add_spacer(height=2)

    #
    # --- donation window
    #
    with dpg.window(
        tag="donationWindow",
        label="Donation",
        modal=True,
        min_size=(scaled(780), scaled(300)),
        show=False
    ):
        # Dear ImGui can't flow a text around a hyperlink, so the paragraph is broken explicitly
        with dpg.group() as supportParagraph:
            # the offset from the top that a standalone text would get,
            # which the inline theme takes away
            dpg.add_spacer(height=scaled(styleFramePadding[1]))
            with dpg.group(horizontal=True):
                dpg.add_text("You can support this project via ")
                add_hyperlink("GitHub Sponsors", sponsorsURL)
                dpg.add_text(" or by donating")
            dpg.add_text("cryptocurrency to either of the following wallets:")
        dpg.bind_item_theme(supportParagraph, getInlineTheme())

        dpg.add_spacer(height=scaled(6))
        # created once here, so clicking doesn't create new themes every time
        copyableTheme = getCopyableTheme()
        copiedTheme = getCopyableTheme(copied=True)
        for currency, address in donationWallets.items():
            with dpg.group(horizontal=True):
                dpg.add_text(f"- {currency}:")
                walletButton = dpg.add_button(
                    label=address,
                    user_data=(address, copyableTheme, copiedTheme),
                    callback=walletAddressClicked
                )
                dpg.bind_item_theme(walletButton, copyableTheme)
                with dpg.tooltip(walletButton):
                    dpg.add_text("Click to copy")

        #dpg.add_spacer(height=scaled(2))
        with dpg.group(horizontal=True):
            dpg.add_text("Signed variant:")
            add_hyperlink(donationSignedURL, donationSignedURL)

        dpg.add_spacer()
        dpg.add_separator()
        dpg.add_spacer(height=scaled(10))
        dpg.add_button(
            label="Close",
            callback=lambda: dpg.hide_item("donationWindow")
        )
        dpg.add_spacer(height=scaled(2))

    #
    # --- about window
    #
    with dpg.window(
        tag="aboutWindow",
        label="About application",
        modal=True,
        min_size=(scaled(780), scaled(440)),
        show=False
    ):
        dpg.add_text(
            "A sandbox application for executing "
            "ADQL queries via TAP interface\n"
            "of various data sources, "
            "such as astronomical databases, using PyVO.\n"
            "Essentially, this is a GUI for PyVO."
        )

        dpg.add_text(f"Version: {__version__}")

        dpg.add_text("License: GPLv3")
        with dpg.group(horizontal=True):
            dpg.add_text("Source code:")
            add_hyperlink(repositoryURL, repositoryURL)

        dpg.add_text(__copyright__)

        dpg.add_spacer()
        dpg.add_separator()
        dpg.add_spacer(height=scaled(5))
        with dpg.group(horizontal=True):
            dpg.add_text("Created with Dear PyGui")
            dpg.add_button(
                label="about that...",
                callback=showDPGabout
            )
        dpg.add_spacer(height=scaled(5))
        dpg.add_separator()
        dpg.add_spacer(height=scaled(10))
        dpg.add_button(
            label="Close",
            callback=lambda: dpg.hide_item("aboutWindow")
        )
        dpg.add_spacer(height=scaled(2))

    # themes/styles bindings
    dpg.bind_font(getGlobalFont())
    dpg.bind_theme(getGlobalTheme())
    dpg.bind_item_theme("errorMessage", getErrorTheme())
    dpg.bind_item_theme("errorMessageSimbadIDs", getErrorTheme())
    dpg.bind_item_theme("donationWindow", getWindowTheme())
    dpg.bind_item_theme("aboutWindow", getWindowTheme())
    # dpg.bind_item_theme("errorDialog", getWindowTheme())
    # dpg.bind_item_theme("errorDialogText", getErrorTheme())

    # mouse clicks handler for results table cells
    with dpg.item_handler_registry(tag="cell-handler"):  # as handler
        dpg.add_item_clicked_handler(callback=cellClicked)

    # keyboard shortcuts
    with dpg.handler_registry():
        # --- Cmd/Ctrl + R for the query text, the callback checks for the modifier
        dpg.add_key_press_handler(dpg.mvKey_R, callback=keyPressCallback)

    # ---

    dpg.create_viewport(
        title="TAP ADQL sandbox",
        width=scaled(1200),
        height=scaled(900),
        min_width=scaled(config.windowMinWidth),
        min_height=scaled(600),
        small_icon=str(applicationPath / "icons/planet-128.ico"),
        large_icon=str(applicationPath / "icons/planet-256.ico")
    )

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window(mainWindowID, True)

    # things to do on application start
    dpg.set_value(
        serviceUrlID,
        tapServices["padc"]["url"]
    )
    dpg.set_value(
        queryTextID,
        tapServices["padc"]["examples"][5]["query"]
    )

    dpg.start_dearpygui()

    dpg.destroy_context()


if __name__ == "__main__":
    main()
