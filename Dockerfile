FROM phiscan:v1

ENV DEBIAN_FRONTEND=noninteractive

RUN rm -r /catkin_ws/src/upd_angle_imu

COPY upd_angle_imu /catkin_ws/src/upd_angle_imu

RUN bash -c "source /opt/ros/noetic/setup.bash && cd /catkin_ws && catkin_make"

RUN rm -r /webapp

COPY webapp/ /webapp

RUN chmod +x /webapp/scripts/*
RUN chmod +x /webapp/start_app.sh

EXPOSE 5000

RUN mkdir -p /var/log/gunicorn

WORKDIR /webapp

# CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "app:app", "--access-logfile", "/var/log/gunicorn/access.log", "--error-logfile", "/var/log/gunicorn/error.log"]
# CMD ["sleep", "infinity"]
CMD ["bash", "start_app.sh"]