import asyncio
import struct
import time


class TimestampSender:
    def __init__(self, ip="10.42.0.233", port=8765, rate_hz=10):
        self.ip = ip
        self.port = port
        self.rate = rate_hz
        self._transport = None
        self._running = False
        self._task = None

    async def start(self, fps):
        self.rate = int(fps)
        if self._running:
            print("Sender already running.")
            return

        self._running = True
        loop = asyncio.get_running_loop()
        self._transport, _ = await loop.create_datagram_endpoint(
            lambda: asyncio.DatagramProtocol(),
            remote_addr=(self.ip, self.port)
        )
        print(f"Started sending to {self.ip}:{self.port} at {self.rate} Hz")
        self._task = asyncio.create_task(self._send_loop())

    async def stop(self):
        if not self._running:
            return

        print("Stopping sender...")
        self._running = False

        if self._task:
            await self._task  # Wait for send loop to finish

        if self._transport:
            self._transport.close()
            self._transport = None
        print("Sender stopped and socket closed.")

    async def _send_loop(self):
        try:
            while self._running:
                now = time.time()
                last_4_before = int(now) % 10000
                frac = int((now - int(now)) * 10000)
                packed = last_4_before * 10000 + frac
                binary_data = struct.pack("<I", packed)

                try:
                    self._transport.sendto(binary_data)
                except Exception as e:
                    print(f"Error sending data: {e}")
                    break

                await asyncio.sleep(1 / self.rate)
        except asyncio.CancelledError:
            print("Send loop cancelled.")
# async def main():
#     sender = TimestampSender()

#     # Handle SIGINT/SIGTERM for graceful shutdown
#     loop = asyncio.get_running_loop()
#     stop_event = asyncio.Event()

#     def signal_handler():
#         stop_event.set()

#     for sig in (signal.SIGINT, signal.SIGTERM):
#         loop.add_signal_handler(sig, signal_handler)

#     await sender.start()

#     await stop_event.wait()
#     await sender.stop()


# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except KeyboardInterrupt:
#         pass