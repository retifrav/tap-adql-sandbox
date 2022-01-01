import dearpygui.dearpygui as dpg
import pathlib
import argparse

from . import applicationPath, settingsFile, mainWindowID
from . import functions as backend
from .theme import setTheme, styleHorizontalPadding, styleScrollbarWidth
from .version import __version__


def main():
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

    dpg.create_context()

    dpg.configure_app(init_file=settingsFile)

    # dpg.set_frame_callback(2, callback=backend.updateGeometry)
    # dpg.set_viewport_resize_callback(callback=backend.updateGeometry)
    dpg.set_exit_callback(callback=lambda: dpg.save_init_file(settingsFile))

    with dpg.window(
        tag=mainWindowID
        # width=900,
        # height=500,
        # no_scrollbar=False  # FIXME doesn't seem to work
    ):
        #
        # --- menu
        #
        with dpg.menu_bar():
            with dpg.menu(label="File"):
                dpg.add_menu_item(label="Save", callback=lambda: print("ololo"))

                with dpg.menu(label="Settings"):
                    dpg.add_menu_item(label="Setting 1", callback=lambda: print("ololo"), check=True)
                    dpg.add_menu_item(label="Setting 2", callback=lambda: print("ololo"))

            if cliArgs.debug:
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

            with dpg.menu(label="About"):
                dpg.add_menu_item(label="DearPyGui", callback=lambda: dpg.show_about())
        #
        # -- contents
        #
        dpg.add_input_text(
            tag="query",
            # hint="ADQL query", # FIXME doesn't work
            # width=700,
            height=350,
            multiline=True,
            tab_input=True
        )
        dpg.add_button(label="Execute query", callback=lambda: print("ololo"))

        dpg.add_text("Query results")

    setTheme()

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
            "query",
            mainWindowWidth - (styleHorizontalPadding * 2 + styleScrollbarWidth)
        )
        # print(f"width: {dpg.get_item_width('query')}")
        dpg.render_dearpygui_frame()
        # to exit
        # dpg.stop_dearpygui()

    dpg.destroy_context()

    raise SystemExit(0)


if __name__ == '__main__':
    main()
