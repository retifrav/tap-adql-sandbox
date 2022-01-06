import dearpygui.dearpygui as dpg
import pathlib
import argparse
import pyvo
import pandas
from tabulate import tabulate
import sys

from .version import __version__
from . import applicationPath, settingsFile
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

lastQueryResults = {}


def showLoading(isLoading):
    if isLoading:
        dpg.configure_item("btnExecuteQuery", show=False)
        dpg.configure_item("loadingAnimation", show=True)
    else:
        dpg.configure_item("loadingAnimation", show=False)
        dpg.configure_item("btnExecuteQuery", show=True)


def executeQuery():
    global lastQueryResults
    lastQueryResults = {}

    dpg.configure_item("resultsGroup", show=False)
    if dpg.does_item_exist("resultsTable"):
        dpg.delete_item("resultsTable")
    dpg.configure_item("errorMessage", show=False)
    dpg.set_value("errorMessage", "")

    dpg.configure_item("menuSaveFile", enabled=False)
    showLoading(True)

    serviceURL = dpg.get_value("serviceURL").strip()
    queryText = dpg.get_value("queryText").strip()

    if not serviceURL:
        dpg.set_value("errorMessage", "No service URL provided")
        dpg.configure_item("errorMessage", show=True)
        showLoading(False)
        return

    if not queryText:
        dpg.set_value("errorMessage", "Cannot execute an empty query")
        dpg.configure_item("errorMessage", show=True)
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
        dpg.configure_item("errorMessage", show=True)
        showLoading(False)
        return

    if debugMode:
        print("\n[DEBUG] Results found:", len(results))
        print(
            tabulate(
                results.to_table(),
                headers=results.fieldnames,
                tablefmt="psql"
            )
        )

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
    dpg.configure_item("resultsGroup", show=True)
    dpg.configure_item("menuSaveFile", enabled=True)


def preFillExample(sender, app_data, user_data):
    dpg.set_value("serviceURL", examplesList[user_data]["serviceURL"])
    dpg.set_value("queryText", examplesList[user_data]["queryText"])


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


def main():
    global debugMode
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
    cliArgs = argParser.parse_args()
    # print(cliArgs)

    debugMode = cliArgs.debug

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
                    tag="menuSaveFile",
                    label="Save results to pickle",
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
                    dpg.add_menu_item(
                        label="exoplanet.eu",
                        user_data="exoplanet.eu",
                        callback=preFillExample
                    )
                    dpg.add_menu_item(
                        label="NASA",
                        user_data="NASA",
                        callback=preFillExample
                    )
                dpg.add_spacer()
                dpg.add_separator()
                dpg.add_spacer()
                dpg.add_menu_item(
                    label="About...",
                    callback=lambda: dpg.configure_item(
                        "aboutWindow",
                        show=True
                    )
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
            tag="queryText",
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
    #         callback=lambda: dpg.configure_item("errorDialog", show=False)
    #     )
    #     dpg.add_spacer(height=2)
    #
    # --- about window
    #
    with dpg.window(
        tag="aboutWindow",
        label="About application",
        modal=True,
        show=False,
        no_title_bar=False
        # no_scrollbar=True
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
                callback=lambda: dpg.show_about()
            )
        dpg.add_spacer(height=5)
        dpg.add_separator()
        dpg.add_spacer(height=10)
        dpg.add_button(
            label="Close",
            callback=lambda: dpg.configure_item("aboutWindow", show=False)
        )
        dpg.add_spacer(height=2)

    # themes/styles bindings
    dpg.bind_font(getGlobalFont())
    dpg.bind_theme(getGlobalTheme())
    dpg.bind_item_theme("errorMessage", getErrorTheme())
    dpg.bind_item_theme("aboutWindow", getWindowTheme())
    # dpg.bind_item_theme("errorDialog", getWindowTheme())
    # dpg.bind_item_theme("errorDialogText", getErrorTheme())

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
