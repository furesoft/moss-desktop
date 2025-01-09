from typing import Dict

from gui.literals import SYNC_STAGE_ICON_TYPES
from rm_api.sync_stages import *

SYNC_STAGE_TEXTS = {
    STAGE_START: "Starting sync",
    STAGE_GET_ROOT: "Getting root",
    STAGE_EXPORT_DOCUMENTS: "Exporting documents",
    STAGE_DIFF_CHECK_DOCUMENTS: "Checking documents",
    STAGE_PREPARE_DATA: "Preparing data",
    STAGE_COMPILE_DATA: "Compiling data",
    STAGE_PREPARE_ROOT: "Preparing root",
    STAGE_PREPARE_OPERATIONS: "Preparing operations",
    STAGE_UPLOAD: "Uploading",
    STAGE_UPDATE_ROOT: "Updating root",
    STAGE_SYNC: "Syncing",
}

SYNC_STAGE_ICONS: Dict[int, SYNC_STAGE_ICON_TYPES] = {
    STAGE_START: "pencil_inverted",
    STAGE_GET_ROOT: "import_inverted",
    STAGE_EXPORT_DOCUMENTS: "export_inverted",
    STAGE_DIFF_CHECK_DOCUMENTS: "rotate_inverted",
    STAGE_PREPARE_DATA: "export_inverted",
    STAGE_COMPILE_DATA: "pencil_inverted",
    STAGE_PREPARE_ROOT: "filter_inverted",
    STAGE_PREPARE_OPERATIONS: "pencil_inverted",
    STAGE_UPLOAD: "rotate_inverted",
    STAGE_UPDATE_ROOT: "pencil_inverted",
    STAGE_SYNC: "rotate_inverted",
}
