# SCANNER Webapp (Raspberry Pi)

A lightweight Flask-based web interface for controlling and monitoring a sensor stack (IMU, LiDAR, GPS) on a Raspberry Pi. The project includes a browser UI (React in plain JS), server endpoints to start/stop processes, helpers to record GPS UBX data, and utility scripts for launching and probing hardware.

## Key features

- Web UI served from `static/html/index.html` for device control and rosbag management.
- REST endpoints to start/stop subsystems: IMU, LiDAR, ROS core, PTP daemon, recording, and more.
- GPS UBX recording via `scripts/record_gps.py`.
- A small UDP/async timestamp sender used by other components: `time_stamp_sender.py` / `ws_server.py` (udp_server variant).

## Prerequisites

- Python 3.8+ (project calls `/usr/bin/python3.8` in a few places).
- Linux (targeted for Raspberry Pi OS / Debian-based distributions).
- Hardware drivers and utilities depending on your sensors (serial access, ROS if you plan to use `roscore`).
- Python packages (install using pip):

```
pip3 install flask requests psutil pyserial pyubx2
```

- Optional system packages you may need:

- `ros-noetic` (if you use the in-repo calls to `roscore`)
- `ptpd` if you plan to use PTP (`/ptpd/on` endpoint uses it)

Install system deps on Debian/Raspbian:

```
sudo apt update
sudo apt install -y python3-venv python3-pip ptpd
```

Note: adjust for your specific environment and ROS installation instructions.

## Quick start

1. From the project root (`/home/phi-machine/.../webapp`), install Python dependencies:

```
pip3 install -r requirements.txt  # create if desired, or run pip3 install commands above
```

2. Run the app (development):

```
./start_app.sh
```

`start_app.sh` invokes `python3 app.py` by default. For production you can run a WSGI server (e.g. Gunicorn) — a commented example is present in `start_app.sh`.

3. Open a browser to the Raspberry Pi IP (port 5000 by default) to access the UI (served from `static/html/index.html`).

## Main files and purpose

- `app.py` — Flask app providing REST endpoints to control IMU, LiDAR, PTPD, roscore and recording. Reads configuration from `config.json`.
- `config.json` — basic config (e.g. default `lidarRPM`, `direction`, `velocity`).
- `start_app.sh` — simple startup script (calls `python3 app.py`).
- `time_stamp_sender.py` — asyncio UDP sender used to send timestamps.
- `ws_server.py` — commented WebSocket server and an active UDP timestamp sender (`udp_server` variant).
- `scripts/` — helper shell and python scripts. Notable ones referenced from `app.py`:
  - `launch_imu.sh`, `launch_lidar.sh` — used to start sensor-related processes
  - `echo_imu.sh`, `echo_lidar.sh`, `echo_imu_2.sh` — quick probes used by `/topic-statuses`
  - `record.sh` — wrapper to start rosbag recording (called by `/record/on`)
  - `record_gps.py` — records UBX and text logs from the first serial port found
- `static/html/index.html`, `static/js/index.js` — UI and client-side scripts (React-like code bundled as plain JS/HTML)

## Important endpoints (examples)

- `GET /` — serves the UI (`index.html`).
- `GET /qr` — serves `qr.html`.
- `GET /topic-statuses` — probes IMU/LiDAR topics and returns readiness.
- `GET /ptpd/on` or `/ptpd/off` — start/stop PTP daemon (requires `ptpd` and sudo privileges).
- `GET /lidar/on` or `/lidar/off` — start/stop LiDAR helper script (`scripts/launch_lidar.sh`).
- `GET /imu/on` or `/imu/off` — start/stop IMU helper script.
- `GET /roscore/on` or `/roscore/off` — start/stop ROS core (if installed).
- `GET /record/on` or `/record/off` — start/stop rosbag recording and GPS logging. `record/on` creates `rosbags` entries under `/rosbags` by default.

There are many other endpoints used by the UI for mounting pendrives and managing rosbag files (see `static/js/index.js` for client calls).

## Config and environment notes

- `app.py` reads `config.json` from the project root. Adjust `scanner_ip`, `local_rosbag_path`, `eth_iface`, and `PASSWORD` values in `app.py` and `config.json` as needed for your network and environment.
- `scripts/record_gps.py` picks the first serial port returned by `serial.tools.list_ports.comports()` — ensure your GPS device is the first or modify the script to use a specific port.
- Many endpoints call external system commands (ptpd, roscore, fuser, killall). They may require sudo or specific user privileges.

## Troubleshooting

- Serial permissions: make sure the user has access to `/dev/tty*` (add to `dialout` group):

```
sudo usermod -a -G dialout $USER
```

- If `pyubx2` serial reading fails, confirm correct baud rate and port. The GPS recorder expects 115200.
- If `roscore` calls fail, confirm ROS installation and that `roscore` is on the PATH (the code points to `/opt/ros/noetic/bin/roscore`).
- If endpoints that shell out to scripts don't work, run the script manually from the shell to see stdout/stderr.

## Security & safety notes

- `app.py` contains a hard-coded `PASSWORD` variable used to run `sudo` commands. For production, do NOT keep passwords in source code. Use proper sudoers configuration, environment variables, or system services.
- The Flask app runs shell commands and uses `subprocess` with shell=True in a few places — audit and sanitize before exposing to untrusted networks.

## Next steps / suggestions

- Add a `requirements.txt` and consider adding a `systemd` unit to run the app on boot.
- Replace hard-coded password usage with proper sudoers entries and drop privileges where possible.
- Add small unit tests or simple health-check endpoints to ensure the stack is responsive.

---

If you'd like, I can:

- generate a `requirements.txt` from the imports observed; or
- add a `systemd` service file and example `gunicorn` command for production deployment; or
- create a minimal `Makefile` with setup/run targets.

Tell me which of those you'd like next.
