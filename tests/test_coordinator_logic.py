import importlib.util
import sys
import types
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "custom_components" / "eurofuel"

custom_components_pkg = types.ModuleType("custom_components")
custom_components_pkg.__path__ = [str(ROOT / "custom_components")]
sys.modules.setdefault("custom_components", custom_components_pkg)

eurofuel_pkg = types.ModuleType("custom_components.eurofuel")
eurofuel_pkg.__path__ = [str(PACKAGE_ROOT)]
sys.modules.setdefault("custom_components.eurofuel", eurofuel_pkg)

const_spec = importlib.util.spec_from_file_location(
    "custom_components.eurofuel.const", PACKAGE_ROOT / "const.py"
)
const_module = importlib.util.module_from_spec(const_spec)
const_spec.loader.exec_module(const_module)
sys.modules["custom_components.eurofuel.const"] = const_module

utils_spec = importlib.util.spec_from_file_location(
    "custom_components.eurofuel.utils", PACKAGE_ROOT / "utils.py"
)
utils = importlib.util.module_from_spec(utils_spec)
utils_spec.loader.exec_module(utils)


@dataclass
class Price:
    price: float


@dataclass
class Station:
    station_id: str
    latitude: float
    longitude: float
    prices: dict


def test_find_cheapest_prefers_lowest_price_not_nearest():
    stations = [
        Station("near", 52.0, 5.0, {"diesel": Price(1.90)}),
        Station("far", 52.1, 5.1, {"diesel": Price(1.70)}),
    ]

    result = utils.find_cheapest(stations, 52.0, 5.0)

    assert result["diesel"][0].station_id == "far"
