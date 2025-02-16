# 3rd-party dependencies
#
import dearpygui.dearpygui as dpg
from dearpygui.demo import show_demo
from dearpygui import __version__ as dpgVersion  # get_dearpygui_version()
#
from tabulate import tabulate
import pathlib
import pandas
import pyvo
#
# standard libraries
#
from time import sleep
import argparse
import sys
import traceback
import webbrowser
from packaging.version import Version
import logging
import typing
#
# own stuff
#
from . import config
from . import applicationPath, settingsFile
from .simbad import simbadWindow, showSimbadIDsWindow
from .version import __version__, __copyright__
from .theme import (
    stylePrimaryColor,
    stylePrimaryColorActive,
    getGlobalFont,
    getGlobalTheme,
    getErrorTheme,
    getWindowTheme,
    getCellHighlightedTheme,
    getCellDefaultTheme,
    getHyperlinkTheme,
    styleHorizontalPadding,
    styleScrollbarWidth
)
from .examples import tapServices

mainWindowID: str = "main-window"
queryTextID: str = "query-text"
serviceUrlID: str = "service-url"

repositoryURL: str = "https://github.com/retifrav/tap-adql-sandbox"

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
    global executingQuery

    # logging.debug(f"sender: {sender}, app_data: {app_data}")

    # dpg.is_item_focused
    if not dpg.is_item_active(queryTextID) or executingQuery:
        return

    if dpg.is_key_down(dpg.mvKey_R):
        # executingQuery = True
        logging.debug(
            " ".join((
                "Triggered executing query",
                "from the keyboard shortcut"
            ))
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

    logging.debug(f"Query to execute:\n{queryText}")

    results: pyvo.dal.DALResults = {}
    try:
        service = pyvo.dal.TAPService(serviceURL)
        results = service.search(queryText)
    except Exception as ex:
        logging.debug(f"Query failed: {ex}")
        dpg.set_value("errorMessage", ex)
        dpg.show_item("errorMessage")
        showLoading(False)
        return

    logging.debug(f"Results found: {len(results)}")
    if config.debugMode:
        try:
            # won't look nice with logging.debug(), so it's a print()
            print(
                tabulate(
                    results.to_table(),
                    headers=results.fieldnames,
                    tablefmt="psql",
                    floatfmt=config.tabulateFloatfmtPrecision
                )
            )
        except Exception as ex:
            logging.warning(f"Couldn't print results. {ex}")

    lastQueryResults = results.to_table().to_pandas()
    rowsCount, columnsCount = lastQueryResults.shape
    logging.debug(f"Columns: {columnsCount}, rows: {rowsCount}")
    if (
        # https://github.com/retifrav/tap-adql-sandbox/issues/8
        # https://github.com/retifrav/tap-adql-sandbox/issues/14
        Version(dpgVersion) < Version("2.0.0")
        and
        columnsCount > config.dpgColumnsMax
    ):
        dpg.set_value(
            "errorMessage",
            " ".join((
                "You have requested too many columns in your query.",
                f"Dear PyGui version {dpgVersion} only supports maximum",
                f"{config.dpgColumnsMax} columns in a table, and so trying",
                "to display results for your query will crash",
                "the application. Remove some columns from your SELECT",
                "statement and try again."
            ))
        )
        dpg.show_item("errorMessage")
        showLoading(False)
        return
    try:
        # when there isn't that many columns,
        # squeezed table doesn't look nice
        addHorizontalScroll = (
            dpg.get_item_width(mainWindowID) / columnsCount < 150
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
            if not config.noEnumerationColumn and rowsCount > 1:
                dpg.add_table_column(label="#")
            for header in lastQueryResults.columns:
                dpg.add_table_column(label=header)
            for index, row in lastQueryResults.iterrows():
                # reveal_type(index)
                index = typing.cast(int, index)
                with dpg.table_row():
                    if not config.noEnumerationColumn and rowsCount > 1:
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
        logging.error(f"{errorMsg}. {ex}")
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
    logging.debug(f"app_data: {app_data}")
    # this check might be redundant,
    # as dialog window apparently performs it on its own
    pickleFileDir: pathlib.Path = pathlib.Path(app_data["current_path"])
    if not pickleFileDir.is_dir():
        logging.error(f"The [{pickleFileDir}] directory does not exist")
        return
    pickleFile: pathlib.Path = pickleFileDir / app_data["file_name"]
    try:
        lastQueryResults.to_pickle(pickleFile)
    except Exception as ex:
        logging.error(f"Couldn't save results to [{pickleFile}]: {ex}")
        return


def cellClicked(sender, app_data) -> None:
    # logging.debug(f"sender: {sender}, app_data: {app_data}")

    # mouse right click
    if app_data[0] == 1:
        cellValue = dpg.get_value(app_data[1])
        # logging.debug(f"cellValue: {cellValue}")
        dpg.set_clipboard_text(cellValue)
        dpg.set_value(app_data[1], "[copied]")
        dpg.bind_item_theme(app_data[1], getCellHighlightedTheme())
        sleep(1)
        dpg.bind_item_theme(app_data[1], getCellDefaultTheme())
        dpg.set_value(app_data[1], cellValue)


def showDPGabout() -> None:
    dpg.hide_item("aboutWindow")
    dpg.show_about()


def main() -> None:
    argParser = argparse.ArgumentParser(
        prog="tap-adql-sandbox",
        description=" ".join((
            f"%(prog)s\n{__copyright__}\nA",
            "sandbox application for executing ADQL queries",
            "via TAP interface of various data sources"
        )),
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
        help=" ".join((
            "add artificial first column",
            "to enumerate results (default: %(default)s)"
        ))
    )
    argParser.add_argument(
        "--tbl-flt-prcs",
        metavar=".8f",
        help="floating point precision for tabulate output"
    )
    cliArgs = argParser.parse_args()
    # logging.debug(cliArgs)

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
                    label="About...",
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
            # FIXME doesn't work (yet)
            # https://github.com/hoffstadt/DearPyGui/issues/1519
            hint="ADQL query",
            default_value="".join((
                "SELECT TOP 11 *\n",
                "FROM some_table\n",
                "WHERE some_thing = 1"
            )),
            width=-1,
            height=300,
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
            indent=7,
            color=stylePrimaryColorActive,
            secondary_color=stylePrimaryColor,
            show=False
        )

        dpg.add_spacer()

        dpg.add_text(
            tag="errorMessage",
            default_value="Error",
            # https://github.com/hoffstadt/DearPyGui/issues/1275
            wrap=(config.windowMinWidth - 50),
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
        id="dialogSaveFile",
        directory_selector=False,
        width=800,
        height=600,
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
    # --- about window
    #
    with dpg.window(
        tag="aboutWindow",
        label="About application",
        modal=True,
        min_size=(780, 440),
        show=False
    ):
        dpg.add_text(
            "".join((
                "A sandbox application for executing ",
                "ADQL queries via TAP interface\n",
                "of various data sources, ",
                "such as astronomical databases, using PyVO.\n",
                "Essentially, this is a GUI for PyVO."
            ))
        )

        dpg.add_text(f"Version: {__version__}")

        dpg.add_text("License: GPLv3")
        with dpg.group(horizontal=True):
            dpg.add_text("Source code:")
            add_hyperlink(repositoryURL, repositoryURL)

        dpg.add_text(__copyright__)

        dpg.add_spacer()
        dpg.add_separator()
        dpg.add_spacer(height=5)
        with dpg.group(horizontal=True):
            dpg.add_text("Created with Dear PyGui")
            dpg.add_button(
                label="about that...",
                callback=showDPGabout
            )
        dpg.add_spacer(height=5)
        dpg.add_separator()
        dpg.add_spacer(height=10)
        dpg.add_button(
            label="Close",
            callback=lambda: dpg.hide_item("aboutWindow")
        )
        dpg.add_spacer(height=2)

    # themes/styles bindings
    dpg.bind_font(getGlobalFont())
    dpg.bind_theme(getGlobalTheme())
    dpg.bind_item_theme("errorMessage", getErrorTheme())
    dpg.bind_item_theme("errorMessageSimbadIDs", getErrorTheme())
    dpg.bind_item_theme("aboutWindow", getWindowTheme())
    # dpg.bind_item_theme("errorDialog", getWindowTheme())
    # dpg.bind_item_theme("errorDialogText", getErrorTheme())

    # mouse clicks handler for results table cells
    with dpg.item_handler_registry(tag="cell-handler") as handler:
        dpg.add_item_clicked_handler(callback=cellClicked)

    # keyboard shortcuts
    with dpg.handler_registry():
        # --- for the query text
        # Mac OS | Control
        dpg.add_key_press_handler(341, callback=keyPressCallback)
        # Mac OS | left Command
        dpg.add_key_press_handler(343, callback=keyPressCallback)
        # Mac OS | right Command
        dpg.add_key_press_handler(347, callback=keyPressCallback)
        # Linux | right Ctrl?
        dpg.add_key_press_handler(345, callback=keyPressCallback)
        # Windows | left and right Ctrl
        dpg.add_key_press_handler(17, callback=keyPressCallback)

    # ---

    dpg.create_viewport(
        title="TAP ADQL sandbox",
        width=1200,
        height=900,
        min_width=config.windowMinWidth,
        min_height=600,
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
