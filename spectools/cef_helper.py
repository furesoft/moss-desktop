# cef_helper.py

import importlib.util
import os


def get_cefpython_path():
    spec = importlib.util.find_spec("cefpython3")
    if spec is None:
        raise ImportError("cefpython3 package not found!")

    cef_path = os.path.dirname(spec.origin)
    return cef_path
