"""Regression tests for previously broken compatibility platform modules."""

import importlib
import pkgutil

from dairyos.domain.events import Event


def test_all_production_modules_import_after_runtime_configuration():
    import dairyos

    errors = []
    for module_info in pkgutil.walk_packages(
        dairyos.__path__, dairyos.__name__ + "."
    ):
        try:
            importlib.import_module(module_info.name)
        except (Exception, SystemExit) as exc:  # Report every broken module together.
            errors.append(
                f"{module_info.name}: {type(exc).__name__}: {exc}"
            )

    assert errors == []
