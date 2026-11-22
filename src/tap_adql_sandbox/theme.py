# 3rd-party dependencies
#
import dearpygui.dearpygui as dpg

# own stuff
#
from . import applicationPath
from .scaling import scaled

styleRounding: int = 0
stylePrimaryColor: tuple[int, int, int] = (30, 120, 0)
stylePrimaryColorActive: tuple[int, int, int] = (30, 140, 0)
styleSecondaryColor: tuple[int, int, int, int] = (111, 111, 111, 80)
styleSecondaryColorActive: tuple[int, int, int, int] = (111, 111, 111, 100)
styleHighlightColor: tuple[int, int, int] = (255, 255, 0)
styleHorizontalPadding: int = 12
styleFramePadding: tuple[int, int] = (10, 6)
styleScrollbarWidth: int = 16
styleFontSize: int = 24


def loadFont(fileName: str):
    # since Dear PyGui 2.3 glyphs (Cyrillic ones included) are loaded on demand,
    # so the font needs no character range hints
    with dpg.font_registry():
        return dpg.add_font(
            applicationPath / "fonts" / fileName,
            scaled(styleFontSize)
        )


def getGlobalFont():
    return loadFont("JetBrainsMono-Thin.ttf")


# Dear PyGui has no bold style, so bold text is a separate font bound to the item
# with `bind_item_font`. All weights of JetBrains Mono have the same glyph width
# and line metrics, so a bold text takes as many columns as the Thin one and sits
# on the same baseline
def getBoldFont():
    return loadFont("JetBrainsMono-Bold.ttf")


def getGlobalTheme():
    with dpg.theme() as globalTheme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(
                dpg.mvStyleVar_WindowPadding,
                scaled(styleHorizontalPadding), scaled(14),
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_FramePadding,
                scaled(styleFramePadding[0]), scaled(styleFramePadding[1]),
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_ItemSpacing,
                scaled(8), scaled(6),
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_ItemInnerSpacing,
                scaled(5), scaled(4),
                category=dpg.mvThemeCat_Core
            )
            # not changed from Dear ImGui's default (4, 2),
            # only here to be scaled
            dpg.add_theme_style(
                dpg.mvStyleVar_CellPadding,
                scaled(4), scaled(2),
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_GrabMinSize,
                scaled(12),
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_ScrollbarSize,
                scaled(styleScrollbarWidth),
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_ScrollbarRounding,
                scaled(styleRounding),
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_GrabRounding,
                scaled(styleRounding),
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_TabRounding,
                scaled(styleRounding),
                category=dpg.mvThemeCat_Core
            )

            # --- colors
            dpg.add_theme_color(
                dpg.mvThemeCol_TitleBgActive,
                stylePrimaryColor,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_TitleBg,
                (30, 80, 0),
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_TitleBgCollapsed,
                (30, 70, 0),
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_FrameBgHovered,
                styleSecondaryColor,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_FrameBgActive,
                styleSecondaryColorActive,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_CheckMark,
                stylePrimaryColor,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_SliderGrab,
                stylePrimaryColor,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_SliderGrabActive,
                stylePrimaryColorActive,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_ButtonHovered,
                stylePrimaryColor,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_ButtonActive,
                stylePrimaryColorActive,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_HeaderHovered,
                stylePrimaryColor,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_HeaderActive,
                stylePrimaryColorActive,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_TabHovered,
                stylePrimaryColor,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_TabSelected,
                stylePrimaryColorActive,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_TabDimmed,
                stylePrimaryColor,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_TabDimmedSelected,
                stylePrimaryColorActive,
                category=dpg.mvThemeCat_Core
            )

        return globalTheme


def getErrorTheme():
    with dpg.theme() as errorTheme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(
                dpg.mvThemeCol_Text,
                (255, 30, 30),
                category=dpg.mvThemeCat_Core
            )
        return errorTheme


def getCellHighlightedTheme():
    with dpg.theme() as cellHighlightedTheme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(
                dpg.mvThemeCol_Text,
                styleHighlightColor,
                category=dpg.mvThemeCat_Core
            )
        return cellHighlightedTheme


def getCellDefaultTheme():
    with dpg.theme() as cellDefaultTheme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(
                dpg.mvThemeCol_Text,
                (255, 255, 255),
                category=dpg.mvThemeCat_Core
            )
        return cellDefaultTheme


def getWindowTheme():
    with dpg.theme() as aboutTheme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(
                dpg.mvStyleVar_WindowPadding,
                scaled(styleHorizontalPadding), scaled(4),
                category=dpg.mvThemeCat_Core
            )
        return aboutTheme


def getHyperlinkTheme():
    with dpg.theme() as hyperlinkTheme:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, [0, 0, 0, 0])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [0, 0, 0, 0])
            dpg.add_theme_color(
                dpg.mvThemeCol_ButtonHovered,
                [29, 151, 236, 25]
            )
            dpg.add_theme_color(dpg.mvThemeCol_Text, [29, 151, 236])
        return hyperlinkTheme


# for a paragraph of texts and hyperlinks that has to look like a multiline text.
# Dear PyGui aligns every text to the frame padding, so a standalone text gets
# `FramePadding.y` above and below it, which puts a gap between such lines.
# Here there is no frame padding, so the lines are only as tall as the text
# and the hyperlinks sit on the same baseline, and no item spacing, so the lines
# follow each other without a gap and the items within a line touch (the texts
# carry their own spaces)
def getInlineTheme():
    with dpg.theme() as inlineTheme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(
                dpg.mvStyleVar_FramePadding,
                0, 0,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_ItemSpacing,
                0, 0,
                category=dpg.mvThemeCat_Core
            )
        return inlineTheme


# a button that looks like a text, for copying its label on click
def getCopyableTheme(copied: bool = False):
    with dpg.theme() as copyableTheme:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(
                dpg.mvThemeCol_Button,
                (0, 0, 0, 0),
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_ButtonHovered,
                styleSecondaryColor,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_ButtonActive,
                styleSecondaryColorActive,
                category=dpg.mvThemeCat_Core
            )
            if copied:
                dpg.add_theme_color(
                    dpg.mvThemeCol_Text,
                    styleHighlightColor,
                    category=dpg.mvThemeCat_Core
                )
        return copyableTheme
