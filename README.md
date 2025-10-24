# PHI Scanner System

This project consists of a ROS-based IMU/LIDAR processing system with a web interface for monitoring and control.

## Installation/Setup only ROS & WebApp (Option 1)

The system requires Docker for installation and running. Follow these steps carefully:

1. First, build the base image using `Dockerfile_phiscan_v1`:
   ```bash
   docker build -t phiscan:v1 -f Dockerfile_phiscan_v1 .
   ```

2. After the first image is built, create the final image using `Dockerfile`:
   ```bash
   docker build -t phiscan:v2 -f Dockerfile .
   ```

## Running the System

You can run the system in one of two ways:

### Method 1: Manual Docker Run

Run the following command to start the container:
```bash
docker run -dit --net=host --privileged -p 5000:5000 -v /home/pi/rosbags:/rosbags -v /media/pi:/media/root  --volume=/dev:/dev phiscan:v2
```

### Method 2: System Integration

Simply reboot the system - the container is configured to start automatically.

## Container Configuration Details

The Docker container is configured with:
- Host network access (`--net=host`)
- Privileged mode for hardware access
- Automatic restart policy (`--restart unless-stopped`)
- Port mappings:
  - 5000: Web interface
  - 8765: WebSocket communication
- Volume mounts:
  - `/home/pi/rosbags`: ROS bag storage
  - `/media/pi`: Media storage
  - `/dev`: Device access

## System Components

The system includes:
- ROS-based IMU/LIDAR processing (`upd_angle_imu`)
- Web interface for monitoring and control (`webapp`)
- WebSocket server for real-time communication
- Automated data recording capabilities

## Project Structure

```
├── upd_angle_imu/        # ROS package for sensor processing
├── webapp/               # Web interface and control system
├── Dockerfile           # Final stage Docker configuration
├── Dockerfile_phiscan_v1 # Base stage Docker configuration
```

## Notes

- The system is designed to run as a containerized application
- All hardware access is managed through the Docker container
- Data persistence is maintained through volume mounts
- The system automatically starts on boot

## Installation/Setup RaspberryPi from scratch (Option 2)

Here’s a clean **README.md** based on all the instructions you provided, organized for clarity:

````markdown
# Phiscan Raspberry Pi 5 Setup (Desktop 64-bit, Debian Bookworm)

This guide describes the setup of a Raspberry Pi 5 system for **Phiscan**, including installation of Debian, Docker, required repositories, hotspot setup, and autostart services.

---

## 1. Install Debian

Install the latest **Debian Desktop 64-bit (Bookworm)** on your storage device.

---

## 2. Create User and Add Permissions

Add current user to `dialout` group for serial device access:

```bash
sudo usermod -aG dialout $USER
````

---

## 3. Clone Required Repositories

Clone the following repositories into `/home/pi`:

```bash
cd /home/pi

git clone https://github.com/code8phicode/raspi-webapp.git webapp
git clone https://github.com/code8phicode/upd_angle_imu.git upd_angle_imu
git clone https://github.com/code8phicode/unmount_server.py unmount_server
```

---

## 4. Install Docker

```bash
sudo apt update && sudo apt upgrade -y
sudo apt-get update
sudo apt-get install -y ca-certificates curl

sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
sudo reboot
```

---

## 5. Hotspot Setup

Create hotspot script:

```bash
sudo nano /usr/local/bin/enable_hotspot.sh
```

Add the following:

```bash
SSID="PHIRPI5-WIFI"
PASSWORD="password"
nmcli device wifi hotspot ifname wlan0 ssid "$SSID" password "$PASSWORD"
```

Make it executable:

```bash
sudo chmod +x /usr/local/bin/enable_hotspot.sh
```

Add to crontab for autostart:

```bash
sudo crontab -e
```

Add:

```
@reboot sleep 5 && /bin/bash /usr/local/bin/enable_hotspot.sh
```

---

## 6. Unmount Server Setup

Make unmount script executable:

```bash
sudo chmod +x /home/pi/unmount_server/unmounter.sh
```

Update `sudoers`:

```bash
sudo visudo
```

Add:

```
pi ALL=NOPASSWD: /usr/bin/umount
pi ALL=NOPASSWD: /usr/bin/eject
pi ALL=NOPASSWD: /home/pi/unmounter.sh
```

---

## 7. Docker Setup

### Dockerfile v1

```dockerfile
FROM ros:noetic-perception-focal
ENV DEBIAN_FRONTEND=noninteractive

RUN rm -f /etc/apt/sources.list.d/ros1-latest.list
RUN apt-get update && apt-get install -y \
    git curl zip nano ptpd lsb-release python3-pip libpcap-dev libyaml-cpp-dev

RUN sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list' && \
    curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | apt-key add - && \
    apt-get update

RUN mkdir -p /catkin_ws/src
RUN apt-get update && apt-get install -y ros-noetic-diagnostic-updater ros-noetic-roslint && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/ros-drivers/velodyne /catkin_ws/src/velodyne && cd /catkin_ws/src/velodyne && git checkout master
COPY upd_angle_imu /catkin_ws/src/upd_angle_imu
RUN bash -c "source /opt/ros/noetic/setup.bash && cd /catkin_ws && catkin_make"

RUN pip3 install --upgrade pip
RUN pip3 install flask requests psutil gunicorn pyubx2 pyserial websockets asyncio

COPY webapp/ /webapp
EXPOSE 5000
WORKDIR /webapp
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "app:app"]
```

Build:

```bash
docker build -f Dockerfile_phiscan_v1 -t phiscan:v1 .
```

---

### Dockerfile v2

```dockerfile
FROM phiscan:v1
ENV DEBIAN_FRONTEND=noninteractive

RUN rm -r /catkin_ws/src/upd_angle_imu
COPY upd_angle_imu /catkin_ws/src/upd_angle_imu
RUN bash -c "source /opt/ros/noetic/setup.bash && cd /catkin_ws && catkin_make"

RUN rm -r /webapp
COPY webapp/ /webapp
RUN chmod +x /webapp/scripts/* /webapp/start_app.sh

EXPOSE 5000
RUN mkdir -p /var/log/gunicorn
WORKDIR /webapp
CMD ["bash", "start_app.sh"]
```

Build:

```bash
docker build -f Dockerfile -t phiscan:v2 .
```

---

## 8. Change IP (Optional)

```bash
sudo nmcli con mod "Wired connection 1" ifname eth0 ipv4.addresses 192.168.1.50/24 ipv4.gateway 192.168.1.1 ipv4.dns "8.8.8.8,8.8.4.4" ipv4.method manual connection.autoconnect yes
```

---

## 9. Final Crontab

Edit root crontab:

```bash
sudo crontab -e
```

Add:

```
@reboot sleep 5 && /bin/bash /usr/local/bin/enable_hotspot.sh
@reboot sleep 5 && docker run -dit --net=host --privileged -p 5000:5000 -v /home/pi/rosbags:/rosbags -v /media/pi:/media/root --volume=/dev:/dev phiscan:v2
@reboot /usr/bin/python3 /home/pi/unmount_server/unmount_server.py
```

---

## References

* [Webapp Repository](https://github.com/code8phicode/raspi-webapp)
* [IMU Update Repository](https://github.com/code8phicode/upd_angle_imu)
* [Unmount Server Script](https://github.com/code8phicode/unmount_server.py)

---

**Now your Raspberry Pi 5 is ready with Docker, hotspot, and autostart services for Phiscan.**

```

---

If you want, I can also **make a shorter, one-page “Quick Start README”** suitable for new deployments with only the essential commands. Do you want me to do that?
```
