import dearpygui.dearpygui as dpg
from . import settingsFile


# some magick with frames
# def updateGeometry():
#     mainWindowWidth = 0
#     # guarantee these commands happen in the same frame
#     with dpg.mutex():
#         mainWindowWidth = dpg.get_viewport_client_width()
#         # viewport_height = dpg.get_viewport_client_height()
#         # mainWindowWidth = dpg.get_item_width(mainWindowID)
#     # guarantee these commands happen in another frame
#     dpg.split_frame()
#     # print(f"Width: {viewport_width} | {mainWindowWidth}")
#     dpg.set_item_width(
#         "query",
#         mainWindowWidth - (styleHorizontalPadding * 2 + styleScrollbarWidth)
#     )
