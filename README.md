# satellite-ground-segment

A home simulation of a distributed satellite ground segment. It models a small swarm of satellites orbiting Earth and a ground station that receives their live telemetry.

---

## What this project does

- Simulates a constellation of satellites using real orbital mechanics
- Each satellite calculates its own position (latitude, longitude, altitude) in real time
- Each satellite sends that data over HTTP to a ground station
- The ground station is a simple API that receives and logs the incoming telemetry

---

## Project structure

```
swarm-constellation/
    Dockerfile              builds the container image used by all services
    docker-compose.yaml     spins up the ground station and all four satellites
    src/
        ground_station.py   the ground station, runs a web API on port 8000
        satellite_node.py   one satellite node, designed to run inside Docker
        constellation.py    standalone local script, no Docker needed
```

---

## What each file does

**ground_station.py**
- Runs a FastAPI web server on port 8000
- Exposes a `/telemetry` endpoint that satellites POST their data to
- Logs every incoming data packet to the console
- Also has a `/health` endpoint to confirm it is up

**satellite_node.py**
- Represents a single satellite
- Reads its name and orbit data from environment variables (set in docker-compose)
- Uses the Skyfield library to calculate where it is right now
- Every 5 seconds it sends its position to the ground station via HTTP POST
- If the ground station is unreachable, it logs a warning and tries again next cycle

**constellation.py**
- A simpler standalone script, runs directly on your machine without Docker
- Simulates 3 satellites at once with hardcoded orbit data
- Prints a live telemetry dashboard to the terminal every 2 seconds
- Good for quick testing without needing containers

**Dockerfile**
- Builds a lightweight Python 3.11 container
- Installs skyfield, fastapi, uvicorn, and requests
- Copies all source files into the container
- Used by all services in docker-compose

**docker-compose.yaml**
- Defines 5 services: one ground station and four satellites (ALPHA, BRAVO, CHARLIE, DELTA)
- Each satellite gets a different orbit position via environment variables
- Satellites only start after the ground station is ready

---

## How to run with Docker

Make sure you are inside the right folder first:

```bash
cd swarm-constellation
```

Build and start everything:

```bash
docker compose up --build
```

You will see the ground station start first, then the four satellites come online and begin sending telemetry. All logs appear in the same terminal.

To stop everything, press `Ctrl+C`.

---

## How to run locally (no Docker)

If you just want to test the orbital propagation without containers:

```bash
cd swarm-constellation/src
python constellation.py
```

This runs three satellites directly in your terminal and updates every 2 seconds.

---

## Dependencies

- [skyfield](https://rhodesmill.org/skyfield/) for orbital mechanics
- [FastAPI](https://fastapi.tiangolo.com/) for the ground station API
- [uvicorn](https://www.uvicorn.org/) to serve the API
- [requests](https://requests.readthedocs.io/) for satellite HTTP communication
