import dearpygui.dearpygui as dpg
from typing import Tuple
from . import applicationPath

styleRounding: int = 0
stylePrimaryColor: Tuple[int, int, int] = (30, 120, 0)
stylePrimaryColorActive: Tuple[int, int, int] = (30, 140, 0)
styleSecondaryColor: Tuple[int, int, int, int] = (111, 111, 111, 80)
styleSecondaryColorActive: Tuple[int, int, int, int] = (111, 111, 111, 100)
styleHorizontalPadding: int = 12
styleScrollbarWidth: int = 16


def getGlobalFont():
    with dpg.font_registry():
        with dpg.font(
            applicationPath / "fonts" / "JetBrainsMono-Thin.ttf",
            24
        ) as globalFont:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
            return globalFont


def getGlobalTheme():
    with dpg.theme() as globalTheme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(
                dpg.mvStyleVar_WindowPadding,
                styleHorizontalPadding, 14,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_FramePadding,
                10, 6,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_ItemSpacing,
                8, 6,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_ItemInnerSpacing,
                5, 4,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_GrabMinSize,
                12,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_ScrollbarSize,
                styleScrollbarWidth,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_ScrollbarRounding,
                styleRounding,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_GrabRounding,
                styleRounding,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_TabRounding,
                styleRounding,
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
                dpg.mvThemeCol_TabActive,
                stylePrimaryColorActive,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_TabUnfocused,
                stylePrimaryColor,
                category=dpg.mvThemeCat_Core
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_TabUnfocusedActive,
                stylePrimaryColorActive,
                category=dpg.mvThemeCat_Core
            )

        return globalTheme


def getErrorTheme():
    with dpg.theme() as errorTheme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(
                dpg.mvThemeCol_Text,
                (255, 0, 0),
                category=dpg.mvThemeCat_Core
            )
        return errorTheme


def getCellHighlightedTheme():
    with dpg.theme() as cellHighlightedTheme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(
                dpg.mvThemeCol_Text,
                (255, 255, 0),
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
                styleHorizontalPadding, 4,
                category=dpg.mvThemeCat_Core
            )
        return aboutTheme
