import dearpygui.dearpygui as dpg
import pathlib
import argparse
import pyvo
import pandas
from tabulate import tabulate

from . import applicationPath, settingsFile, mainWindowID
from .theme import (
    getGlobalFont,
    getGlobalTheme,
    getErrorTheme,
    styleHorizontalPadding,
    styleScrollbarWidth
)
from .version import __version__

debugMode = False


def executeQuery():
    dpg.configure_item("queryResults", show=False)
    dpg.configure_item("errorMessage", show=False)
    serviceURL = dpg.get_value("serviceURL")
    queryText = dpg.get_value("queryText")

    if debugMode:
        print(f"[DEBUG] Query to execute:\n{queryText}")

    results = {}
    try:
        service = pyvo.dal.TAPService(serviceURL)
        results = service.search(queryText)
    except Exception as ex:
        dpg.set_value("errorMessage", ex)
        dpg.configure_item("errorMessage", show=True)
        return

    if debugMode:
        print("Results found:", len(results))
        print(
            tabulate(
                results.to_table(),
                headers=results.fieldnames,
                tablefmt="psql"
            )
        )
    dpg.configure_item("queryResults", show=True)


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
    with dpg.window(
        tag=mainWindowID
        # width=900,
        # height=500,
        # no_scrollbar=True  # FIXME doesn't seem to work
    ):
        #
        # --- menu
        #
        with dpg.menu_bar():
            with dpg.menu(label="File"):
                dpg.add_menu_item(label="Exit", callback=lambda: dpg.stop_dearpygui())

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
                        label="Query to exoplanet.eu",
                        callback=lambda: print("ololo")
                    )
                    dpg.add_menu_item(
                        label="Query to NASA",
                        callback=lambda: print("ololo")
                    )
                dpg.add_spacer()
                dpg.add_separator()
                dpg.add_spacer()
                dpg.add_menu_item(
                    label="About...",
                    callback=lambda: dpg.configure_item("about", show=True)
                )
        #
        # -- contents
        #
        dpg.add_input_text(tag="serviceURL", hint="TAP service")
        dpg.add_input_text(
            tag="queryText",
            hint="ADQL query",  # FIXME doesn't work
            default_value="".join((
                "SELECT TOP 11 *\n",
                "FROM some_table\n",
                "WHERE some_thing = 1"
            )),
            # width=700,
            height=350,
            multiline=True,
            tab_input=True
        )
        dpg.add_button(label="Execute query", callback=executeQuery)

        dpg.add_spacer()

        dpg.add_text(
            tag="queryResults",
            default_value="Query results",
            show=False
        )
        dpg.add_text(
            tag="errorMessage",
            default_value="Error",
            show=False
        )
    #
    # --- about window
    #
    with dpg.window(
        tag="about",
        label="About application",
        modal=True,
        show=False,
        no_title_bar=False
        # no_scrollbar=True
    ):
        dpg.add_text(f"Version: {__version__}")
        dpg.add_text(
            " ".join((
                "Description: A sandbox application for executing",
                "ADQL queries\nvia TAP interface of various data sources,",
                "such as astronomical\ndatabases.",
                "Essentially, it's just a GUI for PyVO."
            ))
        )
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
            callback=lambda: dpg.configure_item("about", show=False)
        )

    dpg.bind_font(getGlobalFont())
    dpg.bind_theme(getGlobalTheme())
    dpg.bind_item_theme("errorMessage", getErrorTheme())

    # FIXME https://github.com/hoffstadt/DearPyGui/issues/639
    dpg.create_viewport(
        title="TAP ADQL sandbox",
        width=1280,
        height=800,
        min_width=700,
        min_height=400,
        small_icon=str(applicationPath/"icons/planet-128.ico"),
        large_icon=str(applicationPath/"icons/planet-256.ico")
    )

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window(mainWindowID, True)

    # dpg.start_dearpygui()
    while dpg.is_dearpygui_running():
        mainWindowWidth = dpg.get_viewport_client_width()
        # print(f"widths before: {mainWindowWidth} | {styleHorizontalPadding} | {styleScrollbarWidth}")
        # FIXME https://github.com/hoffstadt/DearPyGui/discussions/1517
        dpg.set_item_width(
            "serviceURL",
            mainWindowWidth - (styleHorizontalPadding * 2 + styleScrollbarWidth)
        )
        dpg.set_item_width(
            "queryText",
            mainWindowWidth - (styleHorizontalPadding * 2 + styleScrollbarWidth)
        )
        # print(f"width: {dpg.get_item_width('query')}")
        dpg.render_dearpygui_frame()
        # to exit
        # dpg.stop_dearpygui()

    dpg.destroy_context()


if __name__ == '__main__':
    main()
