# 3rd-party dependencies
#
import dearpygui.dearpygui as dpg
from astroquery.simbad import Simbad
from tabulate import tabulate
from typing import Optional
#
# standard libraries
#
import sys
import traceback
#
# own stuff
#
from . import config
from .theme import (
    stylePrimaryColor,
    stylePrimaryColorActive
)


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
        if config.debugMode:
            print("\n[DEBUG] IDs found in Simbad:", oidsCnt)
            try:
                print(
                    tabulate(
                        oids,
                        headers=oids.colnames,
                        tablefmt="psql",
                        floatfmt=config.tabulateFloatfmtPrecision
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
                if not config.noEnumerationColumn and oidsCnt > 1:
                    dpg.add_table_column(label="#", init_width_or_weight=0.05)
                for header in oids.colnames:
                    dpg.add_table_column(label=header)
                index: int = 0
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
                        if config.debugMode:
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
                            if config.debugMode:
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
                        if not config.noEnumerationColumn and oidsCnt > 1:
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
            if config.debugMode:
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


def simbadWindow():
    with dpg.window(
        tag="window_simbadIDs",
        label="Simbad IDs",
        min_size=(550, 700),
        show=False,
        on_close=lambda: dpg.show_item("menu_getSimbadIDs")
    ):
        dpg.add_input_text(
            tag="idToLookUpInSimbad",
            hint="ID to lookup in Simbad",
            width=-1,
            default_value=("A2 146" if config.debugMode else "")
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
