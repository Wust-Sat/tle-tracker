import datetime

from pydantic import BaseModel

degrees = float
kilometers = float


class Position(BaseModel):
    timestamp: datetime.datetime
    latitude: degrees
    longitude: degrees
    altitude_km: kilometers
