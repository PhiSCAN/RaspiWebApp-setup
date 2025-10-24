bag_path=$1
source /catkin_ws/devel/setup.bash
rosbag record --split --size=512 /angle /imu/data /imu/data2 /velodyne_points -O $bag_path
