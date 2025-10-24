How to run?
make a docker image using the file Dockefile_phiscan_v1 with image name phiscan:v1
once done use that phiscan:v1 to create another image name phiscan:v2 using Dockerfile
run the phiscan:v2 using the following command
docker run -dit --net=host --privileged --restart unless-stopped -p 5000:5000 -p 8765:8765 -v /home/pi/rosbags:/rosbags -v /media/pi:/media/root  --volume=/dev:/dev phiscan:v2
or just reboot the system