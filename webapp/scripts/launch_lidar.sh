source /catkin_ws/devel/setup.bash
roslaunch velodyne_pointcloud VLP16_points.launch timestamp_first_packet:=true rpm:=$1
