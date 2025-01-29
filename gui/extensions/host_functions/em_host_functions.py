import json
from typing import Any, Annotated

from extism import Json

from . import definitions as d
from ..input_types import context_button_clean


# Configs
@d.host_fn()
@d.transform_to_json
def moss_em_config_get(key: str):
    return d.extension_manager.configs[d.extension_manager.current_extension].get(key)


@d.host_fn()
@d.unpack
def moss_em_config_set(key: str, value: Any):
    d.extension_manager.configs[d.extension_manager.current_extension][key] = value
    if d.extension_manager.current_extension not in d.extension_manager.dirty_configs:
        d.extension_manager.dirty_configs.append(d.extension_manager.current_extension)


@d.host_fn()
def moss_em_get_state() -> Annotated[dict, Json]:
    return json.loads(json.dumps(d.extension_manager.raw_state))


@d.host_fn()
def moss_em_register_extension_button(button: Annotated[dict, Json]):
    button['_extension'] = d.extension_manager.current_extension
    d.extension_manager.extension_buttons.append(context_button_clean(button, append=d.ACTION_APPEND))
