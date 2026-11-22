# standard libraries
#
import logging
import sys
import traceback

# 3rd-party dependencies
#
import dearpygui.dearpygui as dpg
from astroquery.simbad import Simbad
from astroquery.simbad import conf as simbadConf
from tabulate import tabulate

# own stuff
#
from . import config
from .mirrors import addConnectTimeout, tryMirrors
from .scaling import scaled
from .theme import stylePrimaryColor, stylePrimaryColorActive
from .useragent import addUserAgent

logger: logging.Logger = logging.getLogger(__name__)

# for the application's User-Agent (instead of astroquery's one) and the connect timeout
# that `tryMirrors()` gives to the main server. Astroquery has no setting for network
# timeouts (`Simbad.timeout` is the time limit for executing asynchronous queries
# on the server), but `Simbad.tap` creates its PyVO service with this session.
# It is a private attribute of astroquery's `BaseQuery`, which every astroquery service
# has had for years
addConnectTimeout(addUserAgent(Simbad._session))


def querySimbadIDs(server: str, objectID: str):
    Simbad.server = server
    return Simbad.query_objectids(objectID)


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
        dpg.set_value("errorMessageSimbadIDs", "No ID provided.")
        dpg.show_item("errorMessageSimbadIDs")
        dpg.hide_item("loadingAnimationSimbadIDs")
        dpg.show_item("btn_getSimbadIDs")
        return

    oids = None
    try:
        # the configured server (CDS by default) first, then the mirrors
        # that astroquery knows about, only these names pass the validation
        # in the `Simbad.server` setter
        simbadServers: list[str] = [simbadConf.server] + [
            s for s in simbadConf.servers_list if s != simbadConf.server
        ]
        oids = tryMirrors(
            simbadServers,
            lambda server: querySimbadIDs(server, idToLookUpInSimbad)
        )
    except Exception as ex:
        dpg.set_value("errorMessageSimbadIDs", ex)
        dpg.show_item("errorMessageSimbadIDs")
        dpg.hide_item("loadingAnimationSimbadIDs")
        dpg.show_item("btn_getSimbadIDs")
        return

    if oids:
        oidsCnt: int = len(oids)
        logger.debug(f"IDs found in Simbad: {oidsCnt}")
        if config.debugMode:
            try:
                # won't look nice with logger.debug(), so it's a print()
                print(
                    tabulate(
                        oids,
                        headers=oids.colnames,
                        tablefmt="psql",
                        floatfmt=config.tabulateFloatfmtPrecision
                    )
                )
            except Exception as ex:
                logger.warning(f"Couldn't print results. {ex}")

        # before astroquery version 0.4.8 this table had
        # an upper-cased `ID` column key, but starting
        # with version 0.4.8 it is now lower-cased `id`
        #
        # https://github.com/astropy/astropy/issues/17695
        idColumnKey: str = "ID"
        # or compare `astroquery.__version__` with `0.4.7`
        if idColumnKey not in oids.colnames:
            logger.debug(
                "There is no upper-cased [ID] key "
                "in the resulting table, will try "
                "with lower-cased [id] key"
            )
            idColumnKey = idColumnKey.lower()  # "id"
            if idColumnKey not in oids.colnames:
                errorMsg = "Resulting table has neither [ID] nor [id] column"
                logger.error(errorMsg)
                if len(oids.colnames) > 0:
                    logger.debug(
                        "Here are all the columns/keys "
                        "in this table: "
                        f"{', '.join(oids.colnames)}"
                    )
                else:
                    logger.debug(
                        "There are no columns/keys "
                        "in this table at all"
                    )
                dpg.set_value("errorMessageSimbadIDs", f"{errorMsg}.")
                dpg.show_item("errorMessageSimbadIDs")
                dpg.hide_item("loadingAnimationSimbadIDs")
                dpg.show_item("btn_getSimbadIDs")
                return

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

                    with dpg.table_row():
                        if not config.noEnumerationColumn and oidsCnt > 1:
                            with dpg.table_cell():
                                dpg.add_text(default_value=f"{index+1}")
                        with dpg.table_cell():
                            cellID = f"cellSimbadID-{index+1}"
                            dpg.add_text(
                                tag=cellID,
                                default_value=o[idColumnKey]
                            )
                            dpg.bind_item_handler_registry(
                                cellID,
                                "cell-handler"
                            )
                        index += 1
        except Exception as ex:
            errorMsg = "Couldn't generate the results table"
            logger.error(f"{errorMsg}. {ex}")
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
        min_size=(scaled(550), scaled(700)),
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
            style=dpg.mvLoadInd_Ring,
            radius=1.3,
            thickness=1.1,
            # speed=2,
            indent=scaled(5),
            color=stylePrimaryColorActive,
            secondary_color=stylePrimaryColor,
            show=False
        )

        dpg.add_spacer()

        dpg.add_text(
            tag="errorMessageSimbadIDs",
            default_value="Error",
            wrap=0,  # 0 wraps the text at the window edge
            show=False
        )

        with dpg.group(tag="resultsGroupSimbadIDs", show=False):
            dpg.add_text(default_value="Found the following IDs:")
            with dpg.table(tag="resultsTableSimbadIDs"):
                dpg.add_table_column(label="ResultsSimbadIDs")
