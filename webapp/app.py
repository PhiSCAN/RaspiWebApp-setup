from flask import Flask, send_from_directory, jsonify, request
import subprocess
import time
import requests
import os
import psutil
import signal
from time import sleep
import time
import re
from os.path import expanduser
from pyubx2 import UBXReader, UBXMessage
from datetime import datetime
import getpass
import json
import serial
import time
import serial.tools.list_ports
from time_stamp_sender import TimestampSender
import asyncio, threading


serial_port = ""
baud_rate = 115200
ACCEPTABLE_OCCURANCE = 50
consec_fix = 0
duration = 60  # seconds


home = expanduser("~")
app = Flask(__name__, static_folder="static")
# socketio = SocketIO(app, cors_allowed_origins="*", async_handlers=True)
sender = TimestampSender()
# 1) Spin up a dedicated asyncio loop in a background thread
loop = asyncio.new_event_loop()
def _loop_runner():
    asyncio.set_event_loop(loop)
    loop.run_forever()
threading.Thread(target=_loop_runner, daemon=True).start()

scanner_ip = "http://192.168.1.80:3000"
local_rosbag_path = f"/rosbags"

PASSWORD = "raspberry"
eth_iface = "eth0"
pids = {}

root_dir = os.path.dirname(os.path.realpath(__file__))
json_path = f"{root_dir}/config.json"


def get_json_val(key):
    with open(json_path, "r") as file:
        json_data = json.load(file)
        return json_data[key]


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    return [atoi(c) for c in re.split(r"(\d+)", text)]


def check_pid_exists(pid):
    if pid == None:
        return False
    elif psutil.pid_exists(pid):
        return True
    else:
        return False


def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("No serial ports found.")
        return []

    print("Available serial ports:")
    port_list = []
    for port, desc, hwid in sorted(ports):
        print(f"  {port}: {desc} [{hwid}]")
        port_list.append({"port": port, "hwid": hwid})
    return port_list


def check_imu():
    try:
        response = subprocess.run(
            f"/bin/bash -c {root_dir}/scripts/echo_imu.sh".split(" "),
            stdout=subprocess.PIPE,
            timeout=5,
        )
        out_res = response.stdout.decode()
        return "header" in out_res
    except Exception as e:
        print(f"imu excep false {e}")
        return False


def check_imu2():
    try:
        response = subprocess.run(
            f"/bin/bash -c {root_dir}/scripts/echo_imu_2.sh".split(" "),
            stdout=subprocess.PIPE,
            timeout=5,
        )
        out_res = response.stdout.decode()
        print(out_res)
        return "header" in out_res
    except Exception as e:
        print("no imu")
        return False


def check_lidar():
    try:
        response = subprocess.run(
            f"/bin/bash -c {root_dir}/scripts/echo_lidar.sh".split(" "),
            stdout=subprocess.PIPE,
            timeout=5,
        )
        out_res = response.stdout.decode()
        print(out_res)
        return "header" in out_res
    except Exception as e:
        print("no lidar")
        return False


def check_gps():
    global consec_fix
    try:
        ports = list_serial_ports()
        if len(ports) == 0:
            print("no ports")
            return False
        serial_port = ports[0]["port"]
        end_time = time.time() + duration
        with serial.Serial(serial_port, baud_rate, timeout=1) as stream:
            ubr = UBXReader(stream, protfilter=2)

            print("Listening for UBX messages...")
            while True:
                raw_data, parsed_data = ubr.read()
                if isinstance(parsed_data, UBXMessage):
                    # if parsed_data.identity in target_msgs:
                    # print(parsed_data)
                    if parsed_data.identity == "NAV-PVT":
                        if parsed_data.fixType > 2:
                            consec_fix += 1
                            if consec_fix == ACCEPTABLE_OCCURANCE:
                                print(f"GREAT SUCCESS!! {parsed_data.fixType}")
                                stream.close()
                                return True
                        else:
                            if consec_fix != 0:
                                consec_fix = 0
                            print("NO FIX OBTAINED")
                            stream.close()
                            return False
                if time.time() > end_time:
                    print("TIME'S UP STILL NO")
                    stream.close()
                    return False
    except Exception as e:
        print(str(e))
        return False


@app.route("/")
def home():
    return send_from_directory("static/html", "index.html")


@app.route("/qr")
def qr():
    return send_from_directory("static/html", "qr.html")


@app.get("/topic-statuses")
def topic_statuses():
    try:
        sleep(20)
        data = [check_imu(), check_imu2(), check_lidar()]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)})


@app.get("/turn-off-lidarmotor")
def turn_off_lidar_motor():
    try:
        res = requests.get(f"{scanner_ip}/motor/stop", timeout=10)
        res.raise_for_status()
        return jsonify({"success": True, "msg": "request to lidar motor:success"})
    except Exception as e:
        return jsonify({"success": False, "msg": "request to lidar motor:failed"})


@app.post("/change-lidar-rot-speed")
def change_rotation_speed():
    velocity = get_json_val("velocity")
    direction = get_json_val("direction")
    try:
        vel = request.args.get("vel")
    except Exception as e:
        raise Exception("no vel")
    if not (velocity or direction):
        return jsonify({"success": False, "msg": "request to scanner:failed"})
    try:
        res = requests.get(
            # f"{scanner_ip}/change-lidar-rot-speed?dir={direction}&vel={velocity}",
            # f"{scanner_ip}/motor/start?vel=5&d_vol_pwr=12=&d_vol_lim=12&m_vol_lim=3",
            f"{scanner_ip}/motor/start?vel=5&d_vol_pwr=12=&d_vol_lim=12&m_vol_lim={vel}",
            timeout=10,
        )
        res.raise_for_status()
        return jsonify({"success": True, "msg": "request to scanner:success"})
    except Exception as e:
        return jsonify({"success": False, "msg": "request to scanner:failed"})


@app.get("/ptpd/<state>")
def handle_ptpd(state):
    try:
        if state == "on":
            subprocess.Popen(
                f"echo {PASSWORD} | sudo -S mount -a",
                stdout=subprocess.DEVNULL,
                shell=True,
            )
            process = subprocess.Popen(
                f"echo {PASSWORD} | sudo -S ptpd -M -i {eth_iface} -C",
                stdout=subprocess.DEVNULL,
                shell=True,
            )
            pids["ptpd"] = process.pid
            print("ptpd turned on")
            return jsonify({"success": True, "msg": "ptpd turned on"})
        elif state == "off":
            if "ptpd" not in pids:
                raise Exception("ptpd Process Does not Exist")
            if check_pid_exists(pids["ptpd"]):
                # os.killpg(os.getpgid(pids["ptpd"]), signal.SIGTERM)
                pids["ptpd"] = None
                print("ptpd stopped successfully")
                return jsonify({"success": True, "msg": "ptpd turned off"})
            else:
                raise Exception("ptpd Process Does not Exist")
    except Exception as e:
        print(f"ptpd err - {e}")
        return jsonify({"success": False, "msg": "request to ptpd:failed"})


@app.get("/lidar/<state>")
def handle_lidar_state(state):
    try:
        if state == "on":
            try:
                rpm = get_json_val("lidarRPM")
            except Exception as e:
                rpm = 150
            cmd = f"/bin/bash -c '{root_dir}/scripts/launch_lidar.sh {rpm}'"
            process = subprocess.Popen(
                cmd,
                shell=True,
                # cmd.split(" "),
                stdout=subprocess.DEVNULL,
                preexec_fn=os.setsid,
            )
            pids["lidar"] = process.pid
            print("lidar turned on")
            return jsonify({"success": True, "msg": "lidar turned on"})
        elif state == "off":
            if "lidar" not in pids:
                raise Exception("lidar Process Does not Exist")
            if check_pid_exists(pids["lidar"]):
                os.killpg(os.getpgid(pids["lidar"]), signal.SIGTERM)
                pids["lidar"] = None
                print("lidar stopped successfully")
                return jsonify({"success": True, "msg": "lidar turned off"})
            else:
                raise Exception("lidar Process Does not Exist")
    except Exception as e:
        print(f"lidar err - {e}")
        return jsonify({"success": False, "msg": "request to lidar:failed"})


@app.get("/roscore/<state>")
def handle_roscore_state(state):
    try:
        if state == "on":
            cmd = f"/opt/ros/noetic/bin/roscore"
            process = subprocess.Popen(
                cmd.split(" "),
                stdout=subprocess.DEVNULL,
                preexec_fn=os.setsid,
            )
            pids["roscore"] = process.pid
            sleep(5)
            print("roscore turned on")
            return jsonify({"success": True, "msg": "roscore turned on"})
        elif state == "off":
            stop_all_ros_nodes = "killall -9 rosmaster && killall -9 rosout"
            subprocess.Popen(
                stop_all_ros_nodes.split(" "),
                stdout=subprocess.DEVNULL,
                preexec_fn=os.setsid,
                stderr=subprocess.DEVNULL,
            )
            if "roscore" not in pids:
                raise Exception("roscore Process Does not Exist")
            if check_pid_exists(pids["roscore"]):
                os.killpg(os.getpgid(pids["roscore"]), signal.SIGTERM)
                pids["roscore"] = None
                print("roscore stopped successfully")

                return jsonify({"success": True, "msg": "roscore turned off"})
            else:
                raise Exception("roscore Process Does not Exist")
    except Exception as e:
        print(f"roscore err - {e}")
        return jsonify({"success": False, "msg": "request to roscore:failed"})


@app.get("/imu/<state>")
def handle_imu_state(state):
    try:
        if state == "on":
            cmd = f"/bin/bash -c {root_dir}/scripts/launch_imu.sh"
            process = subprocess.Popen(
                cmd.split(" "),
                preexec_fn=os.setsid,
            )
            pids["imu"] = process.pid
            print("imu turned on")
            return jsonify({"success": True, "msg": "imu turned on"})
        elif state == "off":
            try:
                subprocess.check_output(f"fuser -k 1234/udp", shell=True)
                subprocess.check_output(f"fuser -k 1234/udp", shell=True)
            except Exception as e:
                e
            if "imu" not in pids:
                raise Exception("imu Process Does not Exist")
            if check_pid_exists(pids["imu"]):
                os.killpg(os.getpgid(pids["imu"]), signal.SIGTERM)
                pids["imu"] = None
                print("imu stopped successfully")
                return jsonify({"success": True, "msg": "imu turned off"})
            else:
                raise Exception("imu Process Does not Exist")
    except Exception as e:
        print(f"imu err - {e}")
        return jsonify({"success": False, "msg": "request to imu:failed"})


@app.get("/gps/status")
def handle_gps_state():
    try:
        status = check_gps()
        if status:
            return jsonify({"success": True, "msg": "gps turned on"})
        else:
            raise Exception("no gps")
    except Exception as e:
        print(f"gps err - {e}")
        return jsonify({"success": False, "msg": "gps initialization failed"})


@app.get("/record/<state>")
def record_start(state):
    try:
        if state == "on":
            if "record" in pids:
                if check_pid_exists(pids["record"]):
                    raise Exception("Process still running")
            current_datetime = datetime.now().strftime("%d-%b-%Y_%H_%M_%S")
            bag_path = f"{local_rosbag_path}/{current_datetime}"
            gps_path = f"{local_rosbag_path}/{current_datetime}.ubx"
            txt_path = f"{local_rosbag_path}/{current_datetime}.txt"
            bag_cmd = f"/bin/bash -c '{root_dir}/scripts/record.sh {bag_path}'"
            print(bag_cmd)
            bag_process = subprocess.Popen(
                bag_cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                preexec_fn=os.setsid,
            )
            print("rosbag record started")
            pids["record"] = bag_process.pid
            gps_cmd = f"/usr/bin/python3.8 {root_dir}/scripts/record_gps.py --ubx {gps_path} --txt {txt_path}"
            gps_process = subprocess.Popen(
                gps_cmd.split(" "),
                stdout=subprocess.DEVNULL,
                preexec_fn=os.setsid,
            )
            pids["gps_record"] = gps_process.pid
            return jsonify({"success": True, "msg": "rosbag recording started"})
        elif state == "off":
            if "record" in pids:
                if check_pid_exists(pids["record"]) or check_pid_exists(
                    pids["gps_record"]
                ):
                    if check_pid_exists(pids["record"]):
                        os.killpg(os.getpgid(pids["record"]), signal.SIGTERM)
                        pids["record"] = None
                        print("rosbag record STOPPED")
                    elif check_pid_exists(pids["gps_record"]):
                        os.killpg(os.getpgid(pids["gps_record"]), signal.SIGTERM)
                        pids["gps_record"] = None
                        print("GPS record STOPPED")
                    return jsonify({"success": True, "msg": "rosbag stopped"})
                else:
                    raise Exception("rosbag Process Does not Exist")
        raise Exception("route does not exist")
    except Exception as e:
        print(str(e))
        return jsonify({"success": False, "msg": str(e)})


@app.get("/list-pd")
def list_pendrive():
    try:
        pd_list = os.listdir(f"/media/{getpass.getuser()}")
        pd_list.sort(key=natural_keys)
        return jsonify({"success": True, "msg": "pendrive list", "data": pd_list})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)})


@app.get("/unmount-pd")
def unmount_pendrive():
    try:
        pd = request.args.get("pd")
        res = requests.get(
            # f"{scanner_ip}/change-lidar-rot-speed?dir={direction}&vel={velocity}",
            # f"{scanner_ip}/motor/start?vel=5&d_vol_pwr=12=&d_vol_lim=12&m_vol_lim=3",
            f"http://127.0.0.1:8000/unmount?pd={pd}",
            timeout=30,
        )
        resp = res.json()
        return jsonify({"success": True, "msg": "pendrive list", "data": resp})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)})


@app.get("/bags/<action>")
def handle_bags(action):
    try:
        if action == "show-pd":
            # timeout=30,
            pd = request.args.get("pd")
            res = requests.get(f"http://127.0.0.1:8000/list?pd={pd}")
            resp = res.json()
            if resp["success"] == False:
                raise Exception("no list")
            return jsonify(
                {"success": True, "msg": "rosbag list", "data": resp["data"]}
            )
        if action == "show-ld":
            rosbags_list = os.listdir(local_rosbag_path)
            rosbags_list.sort(key=natural_keys)
            return jsonify(
                {"success": True, "msg": "rosbag list", "data": rosbags_list}
            )
        elif action == "delete-ld":
            rosbags_list = os.listdir(local_rosbag_path)
            print("going to delete")
            for rosbag in rosbags_list:
                rm_cmd = f"rm {local_rosbag_path}/{rosbag}"
                a = subprocess.check_output(rm_cmd, shell=True)
            return jsonify({"success": True, "msg": "deleted"})
        elif action == "delete-pd":
            print("going to delete")
            pd = request.args.get("pd")
            res = requests.get(f"http://127.0.0.1:8000/delete?pd={pd}")
            resp = res.json()
            if resp["success"] == False:
                raise Exception("no list")
            return jsonify(
                {"success": True, "msg": "rosbags deleted", "msg": resp["msg"]}
            )
        elif action == "copy":
            print("going to copy")
            pd = request.args.get("pd")
            res = requests.get(f"http://127.0.0.1:8000/copy?pd={pd}")
            resp = res.json()
            if resp["success"] == False:
                raise Exception("no list")
            return jsonify(
                {"success": True, "msg": "rosbag copied", "msg": resp["msg"]}
            )
        raise Exception("route does not exist")
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)})

@app.post("/start-udp")
def start_udp():
    body = request.get_json()
    # body = request.get_json()
    # schedule sender.start() on our long‐lived loop:
    asyncio.run_coroutine_threadsafe(sender.start(int(body['fps'])), loop)
    return jsonify({"success": True, "msg": "Active"})

@app.get("/stop-udp")
def stop_udp():
    # schedule sender.stop() on that same loop:
    asyncio.run_coroutine_threadsafe(sender.stop(), loop)
    return jsonify({"success": True, "msg": "UDP sender stopping…"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
