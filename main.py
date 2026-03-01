from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio

from autocab_methods import (
    get_driver_by_telephone,
    get_driver_id,
    get_callsign,
    get_status_autocab,
    get_licence_id,
    get_last_log_on,
    get_bookings_completed,
    get_bookings_cancelled,
)
from recruitment_methods import get_status_recruitment

app = FastAPI(title="Driver Info API", version="1.0.0")


# --- Schemas ---

class DriverRequest(BaseModel):
    api_autocab: str
    url_recruitment: str
    telephone_number: str


class DriverResponse(BaseModel):
    id_autocab: int
    callsign: str
    id_licence_id: int
    last_log_on: int
    bookings_completed: int
    bookings_cancelled: int
    status_recruitment: str
    status_autocab: str


# --- Endpoint ---

@app.post("/driver-info", response_model=DriverResponse)
async def get_driver_info(request: DriverRequest):
    """
    Recibe credenciales y número de teléfono,
    y retorna la información consolidada del conductor.
    """
    try:
        # 1. Buscar conductor en Autocab por telephone
        driver = await get_driver_by_telephone(request.api_autocab, request.telephone_number)

        # 2. Extraer campos del driver (retorna defaults si no se encontró)
        id_autocab = get_driver_id(driver)
        callsign = get_callsign(driver)
        status_autocab = get_status_autocab(driver)

        # 3. Resto de llamadas en paralelo
        licence_id, last_log_on, bookings_completed, bookings_cancelled, status_recruitment = await asyncio.gather(
            get_licence_id(request.api_autocab, id_autocab),
            get_last_log_on(request.api_autocab, id_autocab),
            get_bookings_completed(request.api_autocab, id_autocab),
            get_bookings_cancelled(request.api_autocab, id_autocab),
            get_status_recruitment(request.url_recruitment, request.telephone_number),
        )

        return DriverResponse(
            id_autocab=id_autocab,
            callsign=callsign,
            id_licence_id=licence_id,
            last_log_on=last_log_on,
            bookings_completed=bookings_completed,
            bookings_cancelled=bookings_cancelled,
            status_recruitment=status_recruitment,
            status_autocab=status_autocab,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))