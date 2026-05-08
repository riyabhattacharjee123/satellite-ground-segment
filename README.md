# satellite-ground-segment

A home simulation of a distributed satellite ground segment. It models a small swarm of satellites orbiting Earth and a ground station that receives their live telemetry.

---

## What this project does

- Simulates a constellation of satellites using real orbital mechanics
- Each satellite calculates its own position (latitude, longitude, altitude) in real time
- Each satellite sends that data over HTTP to a ground station
- The ground station is a simple API that receives and logs the incoming telemetry
- All telemetry is saved to a CSV file on disk so data is not lost when containers stop

---

## Project structure

```
swarm-constellation/
    Dockerfile              builds the container image used by all services
    docker-compose.yaml     spins up the ground station and all four satellites
    requirements.txt        all Python dependencies in one place
    mission_data/
        mission_log.csv                     live telemetry, written automatically
        darmstadt_training_baseline.csv     synthetic temperature data for Darmstadt
    scripts/
        generate_training_data.py   generates the Darmstadt baseline dataset
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
- Every telemetry packet is written to `mission_data/mission_log.csv` with a timestamp
- The CSV is capped at 2500 rows — once full, the oldest row is dropped to make room for the new one
- If the CSV file is missing or unreadable, the ground station logs the error and carries on without crashing
- Logs are structured with timestamps and log levels so they are easy to read in the terminal
- Also has a `/health` endpoint to confirm it is up and a `/` root endpoint

**satellite_node.py**
- Represents a single satellite
- Reads its name and orbit data from environment variables (set in docker-compose)
- Uses the Skyfield library to calculate where it is right now
- Every 5 seconds it calculates its distance to Darmstadt, Germany using the Haversine formula
- If the satellite is within 500 km of Darmstadt, it logs an access window alert
- Sends its position to the ground station via HTTP POST every 5 seconds
- If the ground station is unreachable, it logs a warning and tries again next cycle

**generate_training_data.py**
- A standalone script in the `scripts/` folder, run it once to generate baseline data
- Simulates one full year of hourly surface temperature readings for Darmstadt
- Uses a seasonal sine wave, a daily sine wave, and random noise to make the data realistic
- Saves 8760 rows to `mission_data/darmstadt_training_baseline.csv`
- This file can be used later as a reference to compare against live satellite readings

**requirements.txt**
- Lists all Python packages the project depends on
- Install everything at once with `pip install -r requirements.txt`

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
- The `mission_data/` folder is mounted as a volume so the CSV survives container restarts
- Each service has log rotation configured to cap log file size at 5MB

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

## Checking the mission log

While the simulation is running, telemetry from all four satellites is saved automatically to:

```
swarm-constellation/mission_data/mission_log.csv
```

Each row looks like this:

```
2026-05-07 10:16:45, SAT-ALPHA, 47.92, 52.31, 428.1
```

The columns are: timestamp, satellite name, latitude, longitude, altitude in km.

The file holds the latest 2500 rows. Once it hits that limit, each new row pushes the oldest one out. You can open it in any spreadsheet app or read it in the terminal with:

```bash
cat swarm-constellation/mission_data/mission_log.csv
```

---

## Generating the Darmstadt training baseline

This is a one-time step. It creates a synthetic temperature dataset that represents what normal conditions over Darmstadt look like across a full year.

First, make sure all dependencies are installed:

```bash
pip install -r requirements.txt
```

Then run the script:

```bash
cd swarm-constellation
python3 scripts/generate_training_data.py
```

The output file will appear at:

```
swarm-constellation/mission_data/darmstadt_training_baseline.csv
```

If you get a permission error on the `mission_data/` folder, it is because Docker created that folder as root when you last ran the containers. Fix it with:

```bash
sudo chmod 777 swarm-constellation/mission_data/
```

This gives your user write access to the folder so the script can save the file.

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
- [pandas](https://pandas.pydata.org/) for generating and handling the training dataset
- [numpy](https://numpy.org/) for the sine wave and noise calculations in the training data
