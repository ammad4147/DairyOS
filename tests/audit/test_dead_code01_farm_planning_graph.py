from __future__ import annotations

import importlib.util


def test_farm_planning_graph_prototype_is_not_importable():
    assert importlib.util.find_spec("dairyos.intelligence.farm_planning_graph") is None
