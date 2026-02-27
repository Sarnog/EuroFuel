# EuroFuel Home Assistant integratie

Deze custom component maakt het mogelijk om actuele brandstofprijzen op te halen voor:

- Benzine E5
- Benzine E10
- Diesel
- LPG

en deze te tonen in Home Assistant, inclusief:

- overzicht per tankstation
- goedkoopste station per brandstoftype binnen een instelbare straal rond een `device_tracker`
- prijs, afstand en adres in sensor-attributen

## Installatie

1. Kopieer `custom_components/eurofuel` naar jouw Home Assistant `custom_components` map.
2. Herstart Home Assistant.
3. Voeg **EuroFuel** toe via *Instellingen → Apparaten en diensten → Integraties*.

## API contract

De integratie gebruikt een **EuroFuel-compatible API** endpoint:

- `GET {api_base_url}/stations`
- Query parameters:
  - `lat`
  - `lon`
  - `radius_km`
  - `country_codes` (komma-gescheiden ISO codes)

Voorbeeld response:

```json
{
  "stations": [
    {
      "id": "123",
      "name": "Station Centrum",
      "brand": "Shell",
      "address": "Voorbeeldstraat 1, Utrecht",
      "country_code": "NL",
      "location": {"lat": 52.0907, "lon": 5.1214},
      "prices": {
        "e5": {"price": 1.979, "currency": "EUR"},
        "e10": {"price": 1.899, "currency": "EUR"},
        "diesel": {"price": 1.689, "currency": "EUR"},
        "lpg": {"price": 0.899, "currency": "EUR"}
      }
    }
  ]
}
```

## Entiteiten

- `sensor.<naam>_nearby_stations`: aantal gevonden stations + attribuutlijst met alle stations, afstanden en prijzen.
- `sensor.<naam>_cheapest_e5`
- `sensor.<naam>_cheapest_e10`
- `sensor.<naam>_cheapest_diesel`
- `sensor.<naam>_cheapest_lpg`

De goedkoopste-sensoren bevatten in attributen:

- `station_name`
- `address`
- `distance_km`
- `currency`

## Service

Gebruik de service `eurofuel.find_cheapest` om on-demand het goedkoopste station te zoeken voor een brandstoftype, eventueel met een andere tracker/locatie dan de standaardconfiguratie.

Voorbeeld service call:

```yaml
service: eurofuel.find_cheapest
data:
  fuel_type: diesel
  device_tracker: device_tracker.mijn_auto
  radius_km: 25
  country_codes:
    - NL
    - BE
```

De service response bevat `price`, `distance_km`, `address` en stationgegevens.
