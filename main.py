import os
from datetime import datetime, timezone

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Air Compressor PDM API")

DATABASE_URL = os.getenv("DATABASE_URL")


class SensorData(BaseModel):
    device_id: str
    temperature: float
    voltage: float
    current: float
    recorded_at: datetime | None = None


@app.get("/")
def home():
    return {"message": "Air Compressor PDM API is running"}


@app.post("/api/sensor-data")
def receive_sensor_data(data: SensorData):
    if not DATABASE_URL:
        raise HTTPException(
            status_code=500,
            detail="DATABASE_URL is not configured"
        )

    recorded_at = data.recorded_at or datetime.now(timezone.utc)

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO sensor_readings
                    (device_id, temperature, voltage, current, recorded_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        data.device_id,
                        data.temperature,
                        data.voltage,
                        data.current,
                        recorded_at
                    )
                )
                row_id = cur.fetchone()[0]

        return {
            "status": "success",
            "id": row_id,
            "device_id": data.device_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

