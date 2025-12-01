# # ws_server.py
# import asyncio
# import websockets
# import datetime

# connected_clients = set()

# async def handler(websocket, path):
#     connected_clients.add(websocket)
#     print("added")
#     try:
#         while True:
#             # Send timestamp every 5 seconds
#             timestamp = datetime.datetime.now().timestamp()
#             for client in connected_clients:
#                 await client.send(str(timestamp))
#                 # print(f"sent {timestamp}")
#             await asyncio.sleep(.1)
#     except websockets.exceptions.ConnectionClosed:
#         pass
#     finally:
#         connected_clients.remove(websocket)
#         print("removed")

# start_server = websockets.serve(handler, "0.0.0.0", 8765)  # Listen on all interfaces

# asyncio.get_event_loop().run_until_complete(start_server)
# print("WebSocket server running on ws://127.0.0.1:8765")
# asyncio.get_event_loop().run_forever()


# udp_server.py
import asyncio
import struct
import time
import sys

UDP_IP = "10.42.0.233"
UDP_PORT = 8765

async def send_timestamps(fps):
    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: asyncio.DatagramProtocol(),
        remote_addr=(UDP_IP, UDP_PORT)
    )

    try:
        while True:
            # Extract only the last 4 digits before and 4 after decimal
            now = time.time()
            last_4_before_decimal = int(now) % 10000  # e.g., 7880
            fractional = int((now - int(now)) * 10000)  # e.g., 1494

            # Pack into a single 32-bit unsigned integer: (7880.1494 → 78801494)
            packed = last_4_before_decimal * 10000 + fractional
            # print(packed)
            binary_data = struct.pack("<I", packed)  # Little endian uint32

            transport.sendto(binary_data)
            await asyncio.sleep(1 / fps)
    finally:
        transport.close()

async def main(fps):
    await send_timestamps(fps)

if __name__ == "__main__":
    fps = int(sys.argv[1])
    asyncio.run(main(fps))