import pygameextra as pe


class Ratios:
    def __init__(self, scale):
        """
        Keep in mind that the aspect ratio is 0.75
        The default height is 1000
        The default width is 750 due to the aspect ratio
        These values are then multiplied by the scale
        """

        self.scale = scale

        # GENERAL
        self.bottom_loading_bar_height = int(40 * scale)

        # LOADER
        self.loader_logo_text_size = int(50 * scale)
        self.loader_loading_bar_width = int(200 * scale)
        self.loader_loading_bar_height = int(10 * scale)
        self.loader_loading_bar_padding = int(20 * scale)
        self.code_screen_header_padding = int(50 * scale)
        self.code_screen_spacing = int(10 * scale)
        self.code_screen_info_size = int(30 * scale)

        # MAIN MENU
        self.main_menu_top_height = int(64 * scale)
        self.main_menu_top_padding = int(21 * scale)
        self.main_menu_my_files_folder_padding = int(28 * scale)
        self.main_menu_path_padding = int(0 * scale)
        self.main_menu_path_first_padding = int(5 * scale)
        self.main_menu_my_files_only_documents_padding = int(26 * scale)
        self.main_menu_folder_padding = int(6 * scale)
        self.main_menu_folder_margin_x = int(12 * scale)
        self.main_menu_folder_margin_y = int(20 * scale)
        self.main_menu_document_padding = int(15 * scale)
        self.main_menu_folder_distance = int(184 * scale)
        self.main_menu_folder_height_distance = int(41 * scale)
        self.main_menu_folder_height_last_distance = int(38 * scale)
        self.main_menu_document_height_distance = int(50 * scale)
        self.main_menu_document_width = int(168 * scale)
        self.main_menu_document_height = int(223 * scale)
        self.main_menu_x_padding = int(17 * scale)
        self.main_menu_my_files_size = int(24 * scale)
        self.main_menu_label_size = int(13 * scale)
        self.main_menu_document_title_size = int(15 * scale)
        self.main_menu_document_title_height_margin = int(8 * scale)
        self.main_menu_document_cloud_padding = int(20 * scale)  # 10 on each size (left and right) / (top and bottom)
        self.main_menu_path_size = int(15.8 * scale)

        # Document Viewer
        self.document_viewer_top_draggable_height = int(48 * scale)  # Accurate to device
        self.document_viewer_loading_square = int(100 * scale)
        self.document_viewer_loading_circle_radius = int(5 * scale)
        self.document_viewer_error_font_size = int(20 * scale)

    def pixel(self, value):
        return max(1, int(value * self.scale))

    def pad_button_rect(self, rect: pe.Rect):
        return rect.inflate(self.pixel(20), self.pixel(20))
