from typing import Literal

MAIN_MENU_MODES = Literal['grid', 'list', 'compressed', 'folder']
MAIN_MENU_LOCATIONS = Literal['my_files', 'trash']
PDF_RENDER_MODES = Literal['cef', 'pymupdf', 'none', 'retry']
NOTEBOOK_RENDER_MODES = Literal['rm_lines_svg_inker']
CONTEXT_BAR_DIRECTIONS = Literal['down', 'right']
