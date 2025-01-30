# dependencies
import dearpygui.dearpygui as dpg
from dearpygui.demo import show_demo
from astroquery.simbad import Simbad
from tabulate import tabulate
import pathlib
import pandas
import pyvo
# standard libraries
from time import sleep
import argparse
import sys
import traceback
import webbrowser
import typing

from . import applicationPath, settingsFile
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

debugMode: bool = False
noEnumerationColumn: bool = False

mainWindowID: str = "main-window"
queryTextID: str = "query-text"
serviceUrlID: str = "service-url"

repositoryURL: str = "https://github.com/retifrav/tap-adql-sandbox"

tabulateFloatfmtPrecision: str = "g"

# Dear PyGui (and Dear ImGui) has a limitation of 64 columns in a table
# https://dearpygui.readthedocs.io/en/latest/documentation/tables.html
# https://github.com/ocornut/imgui/issues/2957#issuecomment-758136035
# https://github.com/ocornut/imgui/pull/4876
dpgColumnsMax: int = 64

windowMinWidth: int = 900

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


def getSimbadIDs() -> None:
    dpg.hide_item("resultsGroupSimbadIDs")
    if dpg.does_item_exist("resultsTableSimbadIDs"):
        dpg.delete_item("resultsTableSimbadIDs")
    dpg.hide_item("errorMessageSimbadIDs")
    dpg.set_value("errorMessageSimbadIDs", "")

    dpg.hide_item("btn_getSimbadIDs")
    dpg.show_item("loadingAnimationSimbadIDs")

    idToLookUpInSimbad: str = dpg.get_value("idToLookUpInSimbad").strip()

    if not idToLookUpInSimbad:
        dpg.set_value("errorMessageSimbadIDs", "No ID provided")
        dpg.show_item("errorMessageSimbadIDs")
        dpg.hide_item("loadingAnimationSimbadIDs")
        dpg.show_item("btn_getSimbadIDs")
        return

    oids = None
    try:
        oids = Simbad.query_objectids(idToLookUpInSimbad)
    except Exception as ex:
        dpg.set_value("errorMessageSimbadIDs", ex)
        dpg.show_item("errorMessageSimbadIDs")
        dpg.hide_item("loadingAnimationSimbadIDs")
        dpg.show_item("btn_getSimbadIDs")
        return

    if oids:
        oidsCnt: int = len(oids)
        if debugMode:
            print("\n[DEBUG] IDs found in Simbad:", oidsCnt)
            try:
                print(
                    tabulate(
                        oids,
                        headers=oids.colnames,
                        tablefmt="psql",
                        floatfmt=tabulateFloatfmtPrecision
                    )
                )
            except Exception as ex:
                print(f"[WARNING] Couldn't print results. {ex}")
        try:
            with dpg.table(
                parent="resultsGroupSimbadIDs",
                tag="resultsTableSimbadIDs",
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
                # scrollY=True
            ):
                dpg.add_table_column(label="#", init_width_or_weight=0.05)
                for header in oids.colnames:
                    dpg.add_table_column(label=header)
                index = 0
                for o in oids:
                    # reveal_type(index)

                    oid: Optional[str] = None
                    # before astroquery version 0.4.8 this row was
                    # with an upper-cased `ID` column key, but starting
                    # with version 0.4.8 it is now lower-cased `id`
                    #
                    # https://github.com/astropy/astropy/issues/17695
                    try:  # or compare `astroquery.__version__` with `0.4.7`
                        oid = o["ID"]
                    except KeyError:
                        if debugMode:
                            print(
                                " ".join((
                                    "[DEBUG] There is no upper-cased `ID` key",
                                    "in this row, will try",
                                    "with lower-cased `id` key"
                                ))
                            )
                        try:
                            oid = o["id"]
                        except KeyError:
                            print(
                                " ".join((
                                    "[ERROR] This results row has neither",
                                    "upper-cased `ID` key nor lower-cased",
                                    "`id` key"
                                ))
                            )
                            if debugMode:
                                if len(o.colnames) > 0:
                                    print(
                                        " ".join((
                                            "[DEBUG] Here are all the other",
                                            "keys in this row:",
                                            ", ".join(o.colnames)
                                        ))
                                    )
                                else:
                                    print(
                                        " ".join((
                                            "[DEBUG] There are no other keys",
                                            "in this row"
                                        ))
                                    )
                    if oid is None:
                        continue

                    with dpg.table_row():
                        with dpg.table_cell():
                            dpg.add_text(default_value=f"{index+1}")
                        with dpg.table_cell():
                            cellID = f"cellSimbadID-{index+1}"
                            dpg.add_text(
                                tag=cellID,
                                default_value=oid
                            )
                            dpg.bind_item_handler_registry(
                                cellID,
                                "cell-handler"
                            )
                        index += 1
        except Exception as ex:
            errorMsg = "Couldn't generate the results table"
            print(f"[ERROR] {errorMsg}. {ex}", file=sys.stderr)
            if debugMode:
                traceback.print_exc(file=sys.stderr)
            dpg.set_value(
                "errorMessageSimbadIDs",
                f"{errorMsg}. There might be more details in console/stderr."
            )
            dpg.show_item("errorMessageSimbadIDs")
            dpg.hide_item("loadingAnimationSimbadIDs")
            dpg.show_item("btn_getSimbadIDs")
            return
        dpg.hide_item("loadingAnimationSimbadIDs")
        dpg.show_item("btn_getSimbadIDs")
        dpg.show_item("resultsGroupSimbadIDs")
    else:
        dpg.set_value(
            "errorMessageSimbadIDs",
            "Simbad doesn't have any IDs for this object"
        )
        dpg.show_item("errorMessageSimbadIDs")
        dpg.hide_item("loadingAnimationSimbadIDs")
        dpg.show_item("btn_getSimbadIDs")
        return


def showSimbadIDsWindow() -> None:
    dpg.hide_item("menu_getSimbadIDs")
    dpg.show_item("window_simbadIDs")


def keyPressCallback(sender, app_data) -> None:
    global executingQuery

    # print(sender, app_data)
    # dpg.is_item_focused
    if not dpg.is_item_active(queryTextID) or executingQuery:
        return

    if dpg.is_key_down(dpg.mvKey_R):
        # executingQuery = True
        if debugMode:
            print(
                "".join((
                    "[DEBUG] Triggered executing query ",
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
        dpg.set_value("errorMessage", "No service URL provided")
        dpg.show_item("errorMessage")
        showLoading(False)
        return

    if not queryText:
        dpg.set_value("errorMessage", "Cannot execute an empty query")
        dpg.show_item("errorMessage")
        showLoading(False)
        return

    if debugMode:
        print(f"\n[DEBUG] Query to execute:\n{queryText}")

    results: pyvo.dal.DALResults = {}
    try:
        service = pyvo.dal.TAPService(serviceURL)
        results = service.search(queryText)
    except Exception as ex:
        if debugMode:
            print(f"\n[DEBUG] Query failed: {ex}")
        dpg.set_value("errorMessage", ex)
        dpg.show_item("errorMessage")
        showLoading(False)
        return

    if debugMode:
        print("\n[DEBUG] Results found:", len(results))
        try:
            print(
                tabulate(
                    results.to_table(),
                    headers=results.fieldnames,
                    tablefmt="psql",
                    floatfmt=tabulateFloatfmtPrecision
                )
            )
        except Exception as ex:
            print(f"[WARNING] Couldn't print results. {ex}")

    lastQueryResults = results.to_table().to_pandas()
    rowsCount, columnsCount = lastQueryResults.shape
    if debugMode:
        print(f"[DEBUG] Columns: {columnsCount}, rows: {rowsCount}")
    if columnsCount > dpgColumnsMax:
        dpg.set_value(
            "errorMessage",
            " ".join((
                "You have requested too many columns in your query.",
                f"Dear PyGui only supports maximum {dpgColumnsMax} columns",
                "in a table, and so trying to display results for your query",
                "will crash the application. Remove some columns from your",
                "SELECT statement and try again."
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
            if not noEnumerationColumn and rowsCount > 1:
                dpg.add_table_column(label="#")
            for header in lastQueryResults.columns:
                dpg.add_table_column(label=header)
            for index, row in lastQueryResults.iterrows():
                # reveal_type(index)
                index = typing.cast(int, index)
                with dpg.table_row():
                    if not noEnumerationColumn and rowsCount > 1:
                        with dpg.table_cell():
                            dpg.add_text(default_value=f"{index+1}")
                    cellIndex = 1
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
        print(f"[ERROR] {errorMsg}. {ex}", file=sys.stderr)
        if debugMode:
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
    if debugMode:
        print(f"[DEBUG] {app_data}")
    # this check might be redundant,
    # as dialog window apparently performs it on its own
    pickleFileDir: pathlib.Path = pathlib.Path(app_data["current_path"])
    if not pickleFileDir.is_dir():
        print(
            f"[ERROR] The {pickleFileDir} directory does not exist",
            file=sys.stderr
        )
        return
    pickleFile: pathlib.Path = pickleFileDir / app_data["file_name"]
    try:
        lastQueryResults.to_pickle(pickleFile)
    except Exception as ex:
        print(
            f"[ERROR] Couldn't save results to {pickleFile}: {ex}",
            file=sys.stderr
        )
        return


def cellClicked(sender, app_data) -> None:
    # print(sender, app_data)

    # mouse right click
    if app_data[0] == 1:
        cellValue = dpg.get_value(app_data[1])
        # print(cellValue)
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
    global debugMode
    global tabulateFloatfmtPrecision
    global noEnumerationColumn

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
    # print(cliArgs)

    debugMode = cliArgs.debug
    noEnumerationColumn = cliArgs.no_enum_column
    if cliArgs.tbl_flt_prcs:
        tabulateFloatfmtPrecision = cliArgs.tbl_flt_prcs

    dpg.create_context()

    dpg.configure_app(init_file=settingsFile)

    # dpg.set_frame_callback(2, callback=updateGeometry)
    # dpg.set_viewport_resize_callback(callback=updateGeometry)
    dpg.set_exit_callback(callback=lambda: dpg.save_init_file(settingsFile))

    #
    # --- Simbad IDs window
    #
    with dpg.window(
        tag="window_simbadIDs",
        label="Simbad IDs",
        min_size=(550, 650),
        show=False,
        on_close=lambda: dpg.show_item("menu_getSimbadIDs")
    ):
        dpg.add_input_text(
            tag="idToLookUpInSimbad",
            hint="ID to lookup in Simbad",
            width=-1
        )
        dpg.add_button(
            tag="btn_getSimbadIDs",
            label="Lookup",
            callback=getSimbadIDs
        )
        dpg.add_loading_indicator(
            tag="loadingAnimationSimbadIDs",
            style=1,
            radius=1.5,
            # speed=2,
            indent=7,
            color=stylePrimaryColorActive,
            secondary_color=stylePrimaryColor,
            show=False
        )

        dpg.add_spacer()

        dpg.add_text(
            tag="errorMessageSimbadIDs",
            default_value="Error",
            # https://github.com/hoffstadt/DearPyGui/issues/1275
            wrap=500,  # window width - 50
            show=False
        )

        with dpg.group(tag="resultsGroupSimbadIDs", show=False):
            dpg.add_text(default_value="Found the following IDs:")
            with dpg.table(tag="resultsTableSimbadIDs"):
                dpg.add_table_column(label="ResultsSimbadIDs")
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

            if debugMode:
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
            wrap=windowMinWidth-50,
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
        height=800,
        min_width=windowMinWidth,
        min_height=600,
        small_icon=str(applicationPath/"icons/planet-128.ico"),
        large_icon=str(applicationPath/"icons/planet-256.ico")
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
