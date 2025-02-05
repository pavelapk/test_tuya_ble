import asyncio
import logging

import grpc.aio
from bleak import BleakClient, BleakScanner, BleakError
from bleak_retry_connector import BLEAK_RETRY_EXCEPTIONS as BLEAK_EXCEPTIONS, get_device

from button import async_setup_buttons
from devices import TuyaBLEData, get_device_product_info, TuyaBLECoordinator
from switch import async_setup_switches

from generated import ble_pb2_grpc as ble_grpc
from generated import ble_pb2 as ble_models

from ha_mock import HASSTuyaBLEDeviceManager
from keyboard_thread import KeyboardThread
from tuya_ble import TuyaBLEDevice

address_cube_touch = "DC:23:4E:8B:60:8F"  # cube touch
address_smart_lock = "DC:23:4D:7B:E1:CE"  # smart lock

# MODEL_NBR_UUID = "00002A00-0000-1000-8000-00805F9B34FB"

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

_cleanup_coroutines = []


class MyService(ble_grpc.MyServiceServicer):

    def __init__(self, query_queue: asyncio.Queue):
        self.query_queue = query_queue

    async def query(self, request: ble_models.QueryRequest,
                    context: grpc.aio.ServicerContext) -> ble_grpc.google_dot_protobuf_dot_empty__pb2.Empty:
        print("query", request)
        await self.query_queue.put(request.message)
        return ble_grpc.google_dot_protobuf_dot_empty__pb2.Empty()


async def get_ble_data_by_address(address: str) -> TuyaBLEData:
    ble_device = await BleakScanner.find_device_by_address(address)
    if not ble_device:
        raise BleakError(f"A device with address {address} could not be found.")

    manager = HASSTuyaBLEDeviceManager()
    device = TuyaBLEDevice(manager, ble_device)
    await device.initialize()

    product_info = get_device_product_info(device)

    coordinator = TuyaBLECoordinator(device)

    try:
        await device.update()
    except BLEAK_EXCEPTIONS as ex:
        raise BleakError(
            f"Could not communicate with Tuya BLE device with address {address}"
        ) from ex

    return TuyaBLEData(
        "ble " + address,
        device,
        product_info,
        coordinator,
    )


async def main():
    # async with BleakClient(address) as client:
    #     model_number = await client.read_gatt_char(MODEL_NBR_UUID)
    #     print("Model Number: {0}".format("".join(map(chr, model_number))))

    # await asyncio.sleep(1)

    # cube_touch_device = await get_ble_data_by_address(address_cube_touch)
    smart_lock_device = await get_ble_data_by_address(address_smart_lock)

    # switches = await async_setup_switches(cube_touch_device)
    switches = await async_setup_switches(smart_lock_device)
    buttons = await async_setup_buttons(smart_lock_device)

    lock_button = buttons[0]
    unlock_button = buttons[1]

    reverse_switch = switches[0]

    # light_switch = switches[0]
    # reverse_switch = switches[1]

    # light_switch.turn_on()
    # await asyncio.sleep(20)
    # light_switch.turn_off()

    query_queue = asyncio.Queue()

    server = grpc.aio.server()
    ble_grpc.add_MyServiceServicer_to_server(MyService(query_queue), server)
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    logging.info("Starting server on %s", listen_addr)
    await server.start()

    async def server_graceful_shutdown():
        logging.info("Starting graceful shutdown...")
        # Shuts down the server with 5 seconds of grace period. During the
        # grace period, the server won't accept new connections and allow
        # existing RPCs to continue within the grace period.
        await server.stop(5)

    _cleanup_coroutines.append(server_graceful_shutdown())
    # await server.wait_for_termination()

    # def my_callback(text: str):
    #     query_queue.put_nowait(text)

    # kthread = KeyboardThread('(on/off) > ', my_callback)

    # for switch in switches:
    #     print("tic", switch)
    #     switch.turn_on()
    #     await asyncio.sleep(5)
    #     switch.turn_off()

    try:
        while True:
            break
            print("wait")
            query = await query_queue.get()
            print("receive")
            if query.startswith("on"):
                # light_switch.turn_on()
                print("turned on")
            elif query.startswith("off"):
                # light_switch.turn_off()
                print("turned off")
            elif query == "lock":
                lock_button.press()
                print("locked")
            elif query == "unlock":
                unlock_button.press()
                print("unlocked")
            elif query == "r true":
                reverse_switch.turn_on()
            elif query == "r false":
                reverse_switch.turn_off()
            elif query == ":q!":
                await smart_lock_device.device.stop()
                # await cube_touch_device.device.stop()
                await server.stop(None)
                # kthread.stop()
                break
            else:
                print("чё ??")
    finally:
        await smart_lock_device.device.stop()
        # await cube_touch_device.device.stop()
        await server.stop(None)
        # kthread.stop()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.run_until_complete(*_cleanup_coroutines)
        loop.close()
