"""
Métodos relacionados con la API de Autocab
"""
import httpx

AUTOCAB_BASE_URL = "https://autocab-api.azure-api.net/booking/v1"
AUTOCAB_DRIVER_URL = "https://autocab-api.azure-api.net/driver/v1"


async def get_driver_by_telephone(api_autocab: str, telephone_number: str) -> dict:
    """
    Llama a la API de Autocab y busca el conductor por telephone.
    Retorna el dict del conductor si lo encuentra, o None si no existe.
    """
    url = f"{AUTOCAB_BASE_URL}/drivers/"
    headers = {
        "Ocp-Apim-Subscription-Key": api_autocab
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        drivers = response.json()

    # Quitar indicativo de país (52) para comparar con lo que tiene Autocab
    local_number = telephone_number.lstrip("+")
    if local_number.startswith("52"):
        local_number = local_number[2:]

    for driver in drivers:
        if driver.get("telephone") == local_number:
            return driver

    return None


def get_driver_id(driver: dict) -> int:
    """Extrae el id_autocab del conductor."""
    if driver is None:
        return 0
    return driver.get("id", 0)


def get_callsign(driver: dict) -> str:
    """Extrae el callsign del conductor."""
    if driver is None:
        return "unknown"
    return driver.get("callsign", "unknown")


def get_status_autocab(driver: dict) -> str:
    """Extrae el status_autocab desde comments.comment1 del conductor."""
    if driver is None:
        return "unknown"
    return driver.get("comments", {}).get("comment2", "unknown")


async def get_licence_id(api_autocab: str, driver_id: int) -> int:
    """
    TODO: Implementar llamada real a Autocab API
    """
    return 0


async def get_last_log_on(api_autocab: str, driver_id: int) -> int:
    """
    Obtiene los días desde el último login del conductor.
    Solo ejecuta la llamada si driver_id > 0.
    """
    if driver_id == 0:
        return 0

    url = f"{AUTOCAB_DRIVER_URL}/driverauthorisations/{driver_id}"
    headers = {"Ocp-Apim-Subscription-Key": api_autocab}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

    last_log_on_str = data.get("lastLogOn")
    if not last_log_on_str:
        return -1

    from datetime import datetime, timezone
    last_log_on = datetime.fromisoformat(last_log_on_str)
    now = datetime.now(timezone.utc)

    # Asegurar que last_log_on tenga timezone para comparar
    if last_log_on.tzinfo is None:
        last_log_on = last_log_on.replace(tzinfo=timezone.utc)

    diff = now - last_log_on
    return diff.days


async def get_bookings_completed(api_autocab: str, driver_id: int) -> int:
    """
    Obtiene el número de bookings completados del conductor.
    Solo ejecuta si driver_id > 0.
    """
    if driver_id == 0:
        return 0
    return await _search_bookings(api_autocab, driver_id, "Completed")


async def get_bookings_cancelled(api_autocab: str, driver_id: int) -> int:
    """
    Obtiene el número de bookings cancelados del conductor.
    Solo ejecuta si driver_id > 0.
    """
    if driver_id == 0:
        return 0
    return await _search_bookings(api_autocab, driver_id, "Cancelled")


async def _search_bookings(api_autocab: str, driver_id: int, booking_type: str) -> int:
    from datetime import datetime, timezone

    url = f"{AUTOCAB_BASE_URL}/1.2/search"
    headers = {
        "Ocp-Apim-Subscription-Key": api_autocab,
        "Content-Type": "application/json",
    }

    total = 0
    continuation_token = None

    while True:
        payload = {
            "from": "2025-06-10T00:00:00Z",
            "to": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.999Z"),
            "telephoneNumber": "",
            "driverId": driver_id,
            "types": [booking_type],
        }

        if continuation_token:
            payload["continuationToken"] = continuation_token

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        total += len(data.get("bookings", []))

        continuation_token = data.get("continuationToken")
        if not continuation_token:
            break

    return total