"""Discover engine classes from the engine package without a central list."""

import importlib
import inspect
import pkgutil

from . import engines as engine_package
from .models import Engine


def engines():
    installed = {}
    for module_info in pkgutil.iter_modules(engine_package.__path__):
        if module_info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{engine_package.__name__}.{module_info.name}")
        for _, candidate in inspect.getmembers(module, inspect.isclass):
            if candidate is Engine or not issubclass(candidate, Engine) or candidate.__module__ != module.__name__:
                continue
            instance = candidate()
            if not instance.id or instance.id == "base":
                raise ValueError(f"{candidate.__name__} must declare a unique engine id")
            if instance.id in installed:
                raise ValueError(f"duplicate engine id: {instance.id}")
            installed[instance.id] = instance
    return installed


def get(engine_id: str):
    try:
        return engines()[engine_id]
    except KeyError as exc:
        raise KeyError(f"unknown engine '{engine_id}'; installed: {', '.join(sorted(engines()))}") from exc
