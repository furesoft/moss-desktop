import json
from typing import Any, Annotated

from extism import Json

from . import definitions as d


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
