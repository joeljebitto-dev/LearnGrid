from __future__ import annotations

import importlib
from typing import Callable

from django.conf import settings


def load_handler(handler_name: str) -> Callable:
    handler_map = getattr(settings, "KAFKA_EVENT_HANDLERS", {})
    dotted_path = handler_map.get(handler_name, handler_name)
    module_name, function_name = dotted_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, function_name)
