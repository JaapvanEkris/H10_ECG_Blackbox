import asyncio
from bleak import BleakScanner, BleakClient
from bleakheart import PolarMeasurementData, BatteryLevel

async def main():
    dev = await BleakScanner.find_device_by_filter(
        lambda d, ad: d.name and "Polar" in d.name, timeout=20)
    if dev is None:
        print("not found"); return
    print("found", dev.name, dev.address)
    async with BleakClient(dev) as client:
        print("battery", await BatteryLevel(client).read())
        pmd = PolarMeasurementData(client, ecg_queue=asyncio.Queue())
        print("measurements", await pmd.available_measurements())
        print("ECG settings", await pmd.available_settings('ECG'))

asyncio.run(main())
