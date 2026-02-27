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


def _station(station_id: str, lat: float, lon: float, e5: float | None, diesel: float | None):
    prices = {}
    if e5 is not None:
        prices["e5"] = Price(price=e5)
    if diesel is not None:
        prices["diesel"] = Price(price=diesel)
    return Station(station_id=station_id, latitude=lat, longitude=lon, prices=prices)


def test_distance_km_zero():
    assert utils.distance_km(52.0, 5.0, 52.0, 5.0) == 0


def test_find_cheapest_per_fuel_type():
    stations = [
        _station("a", 52.0, 5.0, e5=2.0, diesel=1.8),
        _station("b", 52.01, 5.01, e5=1.95, diesel=1.82),
        _station("c", 52.02, 5.02, e5=1.98, diesel=1.75),
    ]

    result = utils.find_cheapest(stations, 52.0, 5.0)

    assert result["e5"][0].station_id == "b"
    assert result["diesel"][0].station_id == "c"
    assert result["e10"] is None
    assert result["lpg"] is None
