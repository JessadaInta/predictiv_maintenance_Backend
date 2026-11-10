import os
from datetime import datetime, timezone

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Air Compressor PDM API")

DATABASE_URL = os.getenv("DATABASE_URL")


class SensorData(BaseModel):
    record_id: str = Field(min_length=1, max_length=100)
    device_id: str
    temperature: float
    voltage: float
    current: float
    recorded_at: datetime | None = None


@app.get("/")
def home():
    return {
        "message": "Air Compressor PDM API is running"
    }


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
                    (
                        record_id,
                        device_id,
                        temperature,
                        voltage,
                        current,
                        recorded_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (record_id)
                    DO NOTHING
                    RETURNING id
                    """,
                    (
                        data.record_id,
                        data.device_id,
                        data.temperature,
                        data.voltage,
                        data.current,
                        recorded_at
                    )
                )

                result = cur.fetchone()

                if result:
                    row_id = result[0]
                    duplicate = False
                else:
                    cur.execute(
                        """
                        SELECT id
                        FROM sensor_readings
                        WHERE record_id = %s
                        """,
                        (data.record_id,)
                    )
                    row_id = cur.fetchone()[0]
                    duplicate = True

        return {
            "status": "success",
            "id": row_id,
            "record_id": data.record_id,
            "duplicate": duplicate
        }

    except Exception as e:
        print("Database Error:", str(e))
        raise HTTPException(
            status_code=500,
            detail="Database operation failed"
        )
