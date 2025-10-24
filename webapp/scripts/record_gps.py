from pyubx2 import UBXReader, UBXMessage
import serial
import argparse
import time
import serial.tools.list_ports


serial_port = ""
baud_rate = 115200
parser = argparse.ArgumentParser(description="GPS Recorder")
parser.add_argument("--ubx", type=str, help="ubx Path", required=True)
parser.add_argument("--txt", type=str, help="txt Path", required=True)
args = parser.parse_args()
ubx_output = args.ubx
txt_output = args.txt


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


ports = list_serial_ports()
if len(ports) == 0:
    exit
serial_port = ports[0]["port"]

with serial.Serial(serial_port, baud_rate, timeout=1) as stream:
    ubr = UBXReader(stream, protfilter=2)

    with open(ubx_output, "wb") as ubx_file, open(txt_output, "wb") as txt_file:
        print("Listening for UBX messages...")
        try:
            while True:
                raw_data, parsed_data = ubr.read()
                ubx_file.write(raw_data)
                if isinstance(parsed_data, UBXMessage):
                    if parsed_data.identity == "NAV-PVT":
                        curr_time_ms = time.time() * 1000
                        lat = parsed_data.lat / 1e7  # degrees
                        lon = parsed_data.lon / 1e7  # degrees
                        alt = parsed_data.hMSL / 1e3  # meters
                        time_ms = parsed_data.iTOW
                        print(f"{curr_time_ms} {time_ms} {lat} {lon} {alt}")
                        txt_file.write(
                            f"{curr_time_ms} {time_ms} {lat} {lon} {alt}\n".encode(
                                "utf-8"
                            )
                        )
                        txt_file.flush()

        except Exception as e:
            print(f"Stopped. {e}")
