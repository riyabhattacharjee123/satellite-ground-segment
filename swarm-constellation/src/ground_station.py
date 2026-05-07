from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel

# This tells the server what a satellite data packet looks like
class Telemetry(BaseModel):
    sat_id: str
    lat: float
    lon: float
    alt: float

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Ground Station API is online"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# This is the satellite's data entry point (Telemetry)
@app.post("/telemetry")
async def receive_telemetry(data: Telemetry):
    # This prints the satellite info to the Ground Station logs
    print(f"Incoming: {data.sat_id} | Lat: {data.lat} | Lon: {data.lon}")
    return {"status": "success", "message": "Telemetry logged"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)