import dearpygui.dearpygui as dpg
import pathlib
import argparse
import pyvo
import pandas
from tabulate import tabulate
import sys

from . import applicationPath, settingsFile
from .version import __version__
from .theme import (
    getGlobalFont,
    getGlobalTheme,
    getErrorTheme,
    getWindowTheme,
    styleHorizontalPadding,
    styleScrollbarWidth
)
from .examples import examplesList

debugMode = False

mainWindowID = "main-window"
queryTextID = "query-text"

tabulateFloatfmtPrecision = "g"

lastQueryResults = {}
executingQuery = False


def showLoading(isLoading):
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


def keyPressCallback(sender, app_data):
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


def executeQuery():
    global lastQueryResults
    lastQueryResults = {}

    dpg.hide_item("resultsGroup")
    if dpg.does_item_exist("resultsTable"):
        dpg.delete_item("resultsTable")
    dpg.hide_item("errorMessage")
    dpg.set_value("errorMessage", "")

    dpg.configure_item("menuSaveFile", enabled=False)
    showLoading(True)

    serviceURL = dpg.get_value("serviceURL").strip()
    queryText = dpg.get_value(queryTextID).strip()

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

    results = {}
    try:
        service = pyvo.dal.TAPService(serviceURL)
        results = service.search(queryText)
    except Exception as ex:
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

    showLoading(False)

    lastQueryResults = results.to_table().to_pandas()
    with dpg.table(
        parent="resultsGroup",
        tag="resultsTable",
        header_row=True,
        resizable=True,
        borders_outerH=True,
        borders_innerV=True,
        borders_innerH=True,
        borders_outerV=True,
        policy=dpg.mvTable_SizingStretchProp
    ):
        dpg.add_table_column()
        for header in lastQueryResults:
            dpg.add_table_column(label=header)
        for index, row in lastQueryResults.iterrows():
            with dpg.table_row():
                with dpg.table_cell():
                    dpg.add_text(default_value=f"{index+1}")
                for cell in row:
                    with dpg.table_cell():
                        dpg.add_text(default_value=cell)
    dpg.show_item("resultsGroup")
    dpg.configure_item("menuSaveFile", enabled=True)


def preFillExample(sender, app_data, user_data):
    dpg.set_value("serviceURL", examplesList[user_data]["serviceURL"])
    dpg.set_value(queryTextID, examplesList[user_data]["queryText"])


def saveResultsToPickle(sender, app_data, user_data):
    if debugMode:
        print(f"[DEBUG] {app_data}")
    # this check might be redundant,
    # as dialog window apparently performs it on its own
    pickleFileDir = pathlib.Path(app_data["current_path"])
    if not pickleFileDir.is_dir():
        print(
            f"[ERROR] The {pickleFileDir} directory does not exist",
            file=sys.stderr
        )
        return
    pickleFile = pickleFileDir / app_data["file_name"]
    try:
        lastQueryResults.to_pickle(pickleFile)
    except Exception as ex:
        print(
            f"[ERROR] Couldn't save results to {pickleFile}: {ex}",
            file=sys.stderr
        )
        return


def showDPGabout():
    # https://github.com/retifrav/tap-adql-sandbox/issues/6
    # dpg.hide_item("aboutWindow")
    dpg.show_about()


def main():
    global debugMode
    global tabulateFloatfmtPrecision

    argParser = argparse.ArgumentParser(
        prog="tap-adql-sandbox",
        description=" ".join((
            "%(prog)s  Copyright (C) 2022  retif\nA",
            "sandbox application for executing ADQL queries",
            f"via TAP interface."
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
        help=f"enable debug/dev mode (default: %(default)s)"
    )
    argParser.add_argument(
        "--tbl-flt-prcs",
        metavar=".8f",
        help="floating point precision for tabulate output"
    )
    cliArgs = argParser.parse_args()
    # print(cliArgs)

    debugMode = cliArgs.debug
    if cliArgs.tbl_flt_prcs:
        tabulateFloatfmtPrecision = cliArgs.tbl_flt_prcs

    dpg.create_context()

    dpg.configure_app(init_file=settingsFile)

    # dpg.set_frame_callback(2, callback=updateGeometry)
    # dpg.set_viewport_resize_callback(callback=updateGeometry)
    dpg.set_exit_callback(callback=lambda: dpg.save_init_file(settingsFile))

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

            if debugMode:
                with dpg.menu(label="Dev"):
                    dpg.add_menu_item(
                        label="Items registry",
                        callback=lambda: dpg.show_item_registry()
                    )
                    dpg.add_menu_item(
                        label="Styling",
                        callback=lambda: dpg.show_style_editor()
                    )
                    dpg.add_menu_item(
                        label="ImGui demo",
                        callback=lambda: dpg.show_imgui_demo()
                    )

            with dpg.menu(label="Help"):
                with dpg.menu(label="Examples"):
                    with dpg.menu(label="PADC"):
                        for exmpl in {
                            k: v for k, v in examplesList.items()
                            if k.startswith("padc-")
                        }:
                            dpg.add_menu_item(
                                label=examplesList[exmpl]["description"],
                                user_data=exmpl,
                                callback=preFillExample
                            )
                    with dpg.menu(label="NASA"):
                        for exmpl in {
                            k: v for k, v in examplesList.items()
                            if k.startswith("nasa-")
                        }:
                            dpg.add_menu_item(
                                label=examplesList[exmpl]["description"],
                                user_data=exmpl,
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
            tag="serviceURL",
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
            height=350,
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
            radius=2,
            speed=3,
            indent=10,
            show=False
        )

        dpg.add_spacer()

        dpg.add_text(
            tag="errorMessage",
            default_value="Error",
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
        # https://github.com/retifrav/tap-adql-sandbox/issues/6
        # modal=True,
        show=False
    ):
        dpg.add_text(
            "".join((
                "A sandbox application for executing ",
                "ADQL queries via TAP interface\nof various data sources, ",
                "such as astronomical databases, using PyVO.\n",
                "Essentially, this is a GUI for PyVO."
            ))
        )
        dpg.add_text(f"Version: {__version__}")
        dpg.add_text(f"Source code: https://github.com/retifrav/tap-adql-sandbox")
        dpg.add_text(f"License: GPLv3")
        dpg.add_spacer()
        dpg.add_separator()
        dpg.add_spacer(height=5)
        with dpg.group(horizontal=True):
            dpg.add_text("Created with DearPyGui")
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
    dpg.bind_item_theme("aboutWindow", getWindowTheme())
    # dpg.bind_item_theme("errorDialog", getWindowTheme())
    # dpg.bind_item_theme("errorDialogText", getErrorTheme())

    # keyboard shortcuts
    with dpg.handler_registry():
        # --- for the query text
        # Control
        dpg.add_key_press_handler(341, callback=keyPressCallback)
        # left Command
        dpg.add_key_press_handler(343, callback=keyPressCallback)
        # right Command
        dpg.add_key_press_handler(347, callback=keyPressCallback)

    # ---

    dpg.create_viewport(
        title="TAP ADQL sandbox",
        width=1200,
        height=800,
        min_width=900,
        min_height=600,
        small_icon=str(applicationPath/"icons/planet-128.ico"),
        large_icon=str(applicationPath/"icons/planet-256.ico")
    )

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window(mainWindowID, True)

    dpg.start_dearpygui()

    dpg.destroy_context()


if __name__ == '__main__':
    main()
