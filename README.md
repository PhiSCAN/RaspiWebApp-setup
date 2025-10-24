# PHI Scanner System

This project consists of a ROS-based IMU/LIDAR processing system with a web interface for monitoring and control.

## Installation

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

For detailed information about specific components, please refer to the documentation in respective directories.