from typing import Any

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
