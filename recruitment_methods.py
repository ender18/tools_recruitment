"""
Métodos relacionados con la URL de Recruitment
"""
import httpx


async def get_status_recruitment(url_recruitment: str, telephone_number: str) -> str:
    """
    Llama a la API de recruitment y busca el conductor por phone.
    El phone en recruitment viene como +52XXXXXXXXXX.
    El telephone_number que recibimos ya viene con +52 adelante.
    """
    url = f"{url_recruitment}/api/v1/preleads?page=1&page_size=200000"

    # Normalizar el número para comparar: asegurar que tenga + adelante
    normalized = telephone_number if telephone_number.startswith("+") else f"+{telephone_number}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()

    preleads = data.get("data", [])

    for prelead in preleads:
        phone = prelead.get("phone", "")
        if phone == normalized:
            return prelead.get("recruitment_status", "unknown")

    return "unknown"