debugMode: bool = False

tabulateFloatfmtPrecision: str = "g"

windowMinWidth: int = 900

noEnumerationColumn: bool = False

# older versions of Dear PyGui (and Dear ImGui) have a limitation of 64 columns
# in a table:
# - https://dearpygui.readthedocs.io/en/latest/documentation/tables.html
# - https://github.com/ocornut/imgui/issues/2957#issuecomment-758136035
# - https://github.com/ocornut/imgui/pull/4876
dpgColumnsMax: int = 64
