# satellite-ground-segment

A home simulation of a distributed satellite ground segment. It models a small swarm of satellites orbiting Earth and a ground station that receives their live telemetry.

---

## What this project does

- Simulates a constellation of satellites using real orbital mechanics
- Each satellite calculates its own position (latitude, longitude, altitude) in real time
- Each satellite sends that data over HTTP to a ground station
- The ground station is a simple API that receives and logs the incoming telemetry
- All telemetry is saved to a CSV file on disk so data is not lost when containers stop
- Each satellite carries an AI brain that is trained on a year of synthetic Darmstadt temperature data
- When a satellite flies over Darmstadt, it samples a temperature and asks the AI if it is normal or anomalous
- Anomalous readings are flagged and sent as priority telemetry to the ground station
- All telemetry is stored in a PostgreSQL database for permanent mission history
- A Grafana dashboard visualizes satellite positions on a live world map, total pings, and anomaly alerts
- Apache Airflow runs two automated pipelines: one refreshes the global sensor map every hour, the other builds a clean retraining dataset from flagged anomalies every day
- The sensor map generation and satellite grid calculations use joblib to distribute work across all available CPU cores in parallel
- Terraform in `infra/aws/` sets up AWS for the ground segment: a host in a private subnet with no public IP and no inbound ports, reached over Tailscale (work in progress)
- The AWS setup uses a least-privilege IAM role, a KMS-encrypted S3 bucket for telemetry and CloudTrail audit logging

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
        global_sensor_data.nc               synthetic global temperature map (NetCDF)
    scripts/
        generate_training_data.py   generates the Darmstadt baseline dataset
        generate_sensor_data.py     generates the global NetCDF sensor map
    dags/
        sensor_update_dag.py        Airflow DAG that refreshes the NetCDF sensor map every hour
        anomaly_processing_dag.py   Airflow DAG that builds a retraining payload from anomalies daily
    src/
        ground_station.py   the ground station, runs a web API on port 8000
        satellite_node.py   one satellite node, designed to run inside Docker
        saliency_engine.py  the AI anomaly detection brain used by each satellite
        constellation.py    standalone local script, no Docker needed
infra/
    aws/
        versions.tf             Terraform and AWS provider versions
        variables.tf            region, network ranges, instance size, Tailscale key parameter
        network.tf              VPC, public and private subnets, NAT gateway, S3 endpoint, security group
        iam.tf                  least-privilege role for the host
        storage.tf              KMS key and the encrypted telemetry bucket
        audit.tf                CloudTrail trail and its log bucket
        compute.tf              the Ubuntu host in the private subnet
        user_data.sh.tftpl      first boot: Docker, Tailscale and a copy of this repo
        outputs.tf              instance ID, bucket names, Grafana URL
        README.md               how to deploy it, what it costs, next steps
```

---

## What each file does

**ground_station.py**
- Runs a FastAPI web server on port 8000
- Exposes a `/telemetry` endpoint that satellites POST their data to
- Each telemetry packet can carry: satellite ID, lat, lon, alt, surface temperature, and an anomaly flag
- Writes every telemetry packet to PostgreSQL using SQLAlchemy as the primary store
- Also writes to `mission_data/mission_log.csv` as a backup in case the database is unavailable
- The CSV is capped at 2500 rows — once full, the oldest row is dropped to make room for the new one
- `/health` confirms the API is up
- `/health/stats` queries the database live and returns total telemetry count, total anomaly count, and system status
- Logs are structured with timestamps and log levels so they are easy to read in the terminal

**satellite_node.py**
- Represents a single satellite
- Reads its name and orbit data from environment variables (set in docker-compose)
- On startup, loads the SaliencyEngine and trains it on the Darmstadt baseline data
- Uses the Skyfield library to calculate where it is right now
- Every 5 seconds it calculates its distance to Darmstadt, Germany using the Haversine formula
- Outside the 5000 km range: sends a simple heartbeat with just position data
- Inside the 5000 km range (access window): reads the real surface temperature from the NetCDF map at its current lat/lon using xarray, runs it through the AI, and sends telemetry with an anomaly flag
- Includes a parallel grid search engine using joblib that distributes coordinate evaluations across all CPU cores
- If the ground station is unreachable, it carries on silently and tries again next cycle

**saliency_engine.py**
- The AI brain used by each satellite
- Uses scikit-learn's IsolationForest algorithm trained on one year of Darmstadt temperature history
- Once trained, it can classify any new temperature reading as normal or anomalous
- Uses a 1% contamination threshold, meaning only the most extreme readings get flagged
- If the baseline file is missing, it defaults to treating everything as normal so the satellite does not crash

**generate_training_data.py**
- A standalone script in the `scripts/` folder, run it once to generate baseline data
- Simulates one full year of hourly surface temperature readings for Darmstadt
- Uses a seasonal sine wave, a daily sine wave, and random noise to make the data realistic
- Saves 8760 rows to `mission_data/darmstadt_training_baseline.csv`
- This file is used by the SaliencyEngine to learn what normal temperatures look like

**generate_sensor_data.py**
- Generates a synthetic global surface temperature map and saves it as a NetCDF file
- Creates a 180x360 lat/lon grid with base temperatures modelled on real climate patterns (warm at equator, cold at poles)
- Builds the anomaly mask in parallel using joblib, distributing the 64,800 coordinate evaluations across all available CPU cores
- Injects a heatwave anomaly of 50°C within a 2-degree radius of Darmstadt so the satellites have something to detect
- Saves to `mission_data/global_sensor_data.nc`
- Run this once before starting the Docker simulation so the satellites have a sensor map to read from

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
- Installs system libraries (`libhdf5-dev`, `libnetcdf-dev`) needed to compile the `netCDF4` package
- Copies `requirements.txt` in first and installs all Python dependencies from it
- Copies all source files into the container
- Used by all services in docker-compose

**docker-compose.yaml**
- Defines 9 services: ground station, four satellites (ALPHA, BRAVO, CHARLIE, DELTA), PostgreSQL, Grafana, Airflow webserver, and Airflow scheduler
- Each satellite gets a different orbit position via environment variables
- Satellites only start after the ground station is ready
- The `mission_data/` folder is mounted as a volume on all services so satellites can read the training baseline and the ground station can write the mission log
- PostgreSQL runs on port 5432 with a named volume so data survives container restarts
- Grafana runs on port 3000 and depends on the database being up before it starts
- Airflow webserver runs on port 8080 and shares the same PostgreSQL database for its own metadata
- Both Airflow services mount the `dags/` and `scripts/` folders so pipelines can access the generation scripts
- Each service has log rotation configured to cap log file size at 5MB

**sensor_update_dag.py**
- Runs on an hourly schedule inside Apache Airflow
- Calls the sensor map generator to produce a fresh NetCDF file every hour
- Ensures the satellite constellation always reads from an up-to-date global temperature map

**anomaly_processing_dag.py**
- Runs on a daily schedule inside Apache Airflow
- Connects directly to the PostgreSQL database and pulls all telemetry rows where `is_anomaly = True`
- Cleans the data by dropping rows with missing coordinates and deduplicating by location zone, keeping the highest temperature reading per zone
- Saves the result to `mission_data/retraining_payload.csv` so the AI model can be retrained if climate drift is detected

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
2026-05-07 10:16:45, SAT-ALPHA, 47.92, 52.31, 428.1, 14.3, False
```

The columns are: timestamp, satellite name, latitude, longitude, altitude in km, surface temperature (filled only during access windows), anomaly flag.

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

## Generating the global sensor map

This is also a one-time step, and it must be run before starting Docker. It creates the NetCDF file that satellites use as their digital twin sensor during access windows.

```bash
cd swarm-constellation
python3 scripts/generate_sensor_data.py
```

The output file will appear at:

```
swarm-constellation/mission_data/global_sensor_data.nc
```

The file contains a full global temperature grid with a synthetic 50°C heatwave injected at Darmstadt. When a satellite enters the access window and reads this file at its current coordinates, the AI will flag it as an anomaly and send a priority telemetry packet.

If you get a permission error, run this first:

```bash
sudo chmod 777 swarm-constellation/mission_data/
```

---

## Querying the database

While the simulation is running, you can connect directly to the PostgreSQL container and run SQL queries.

Open a shell inside the database container:

```bash
docker exec -it mission_control_db psql -U mission_user -d mission_telemetry
```

Useful queries once inside:

View the latest 10 telemetry records:

```sql
SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT 10;
```

Count all anomalies detected:

```sql
SELECT COUNT(*) FROM telemetry WHERE is_anomaly = TRUE;
```

See telemetry grouped by satellite:

```sql
SELECT sat_id, COUNT(*) AS pings FROM telemetry GROUP BY sat_id;
```

See only anomalous records with their temperatures:

```sql
SELECT sat_id, timestamp, lat, lon, temp FROM telemetry WHERE is_anomaly = TRUE ORDER BY timestamp DESC;
```

Type `\q` to exit the database shell.

You can also hit the health stats endpoint without entering the container:

```bash
curl http://localhost:8000/health/stats
```

---

## Grafana dashboard

Once the stack is running, open Grafana at `http://localhost:3000` and log in with username `admin` and password `admin`.

To connect it to your database, go to **Connections > Data Sources > Add new > PostgreSQL** and fill in:

- Host: `db:5432`
- Database: `mission_telemetry`
- User: `mission_user`
- Password: `space_password`
- TLS/SSL Mode: disable

The dashboard has three panels:

- **Number of satellite pings** — a stat panel showing the total telemetry count from all four satellites, refreshing every 5 seconds
- **Anomaly Alert** — a stat panel showing the total number of anomalous readings detected across the mission, highlighted in red
- **Satellite live map** — a geomap panel plotting every satellite position as a track across the globe, colour-coded green for normal readings and red for anomalies, so you can see exactly where the heatwave was detected

---

## Apache Airflow

Once the stack is running, open Airflow at `http://localhost:8080` and log in with username `admin` and password `admin`.

Two pipelines run automatically:

**satellite_sensor_ingestion** (runs every hour)
- Regenerates the global NetCDF sensor map so the constellation always has fresh data to sample

**mlops_anomaly_processing** (runs every day)
- Pulls all anomalous telemetry from the database, deduplicates it by location, and saves a clean CSV to `mission_data/retraining_payload.csv`

To trigger either pipeline manually, click the play button next to its name on the DAGs screen.

The retraining payload is what you would feed into a new training run of the IsolationForest model if real-world readings started drifting away from the baseline.

---

## Running on AWS (work in progress)

The `infra/aws/` folder has Terraform that runs the ground segment on a private AWS host. It has no public IP and no open inbound ports; Grafana, Airflow and SSH are reached over Tailscale. See [infra/aws/README.md](infra/aws/README.md) for what it creates and how to deploy it.

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
- [scikit-learn](https://scikit-learn.org/) for the IsolationForest anomaly detection model
- [joblib](https://joblib.readthedocs.io/) for parallel grid processing across CPU cores and model serialisation
- [xarray](https://docs.xarray.dev/) for reading and querying the NetCDF sensor map
- [netCDF4](https://unidata.github.io/netcdf4-python/) as the backend for reading NetCDF files
- [scipy](https://scipy.org/) as a fallback backend for xarray NetCDF support
- [sqlalchemy](https://www.sqlalchemy.org/) for talking to PostgreSQL from Python
- [psycopg2-binary](https://www.psycopg.org/) as the PostgreSQL database driver
