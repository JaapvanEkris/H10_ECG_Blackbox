import asyncio
from bleak import BleakScanner, BleakClient
from bleakheart import PolarMeasurementData

FS = 130.163

async def main():
    dev = await BleakScanner.find_device_by_filter(
        lambda d, ad: d.name and "Polar" in d.name, timeout=20)
    q = asyncio.Queue()
    async with BleakClient(dev) as client:
        pmd = PolarMeasurementData(client, ecg_queue=q)
        err, msg, _ = await pmd.start_streaming('ECG')
        if err != 0:
            print("start failed:", msg); return

        prev_ts = None
        frames = samples = gaps = 0
        t_end = asyncio.get_event_loop().time() + 1200   # 20 min

        while asyncio.get_event_loop().time() < t_end:
            _, ts, data = await q.get()
            frames += 1
            samples += len(data)
            if prev_ts is not None:
                expected = len(data) / FS * 1e9
                drift = (ts - prev_ts) - expected
                if abs(drift) > 0.5 * expected:
                    gaps += 1
                    print(f"gap at {ts}: {(ts-prev_ts)/1e6:.1f} ms "
                          f"vs {expected/1e6:.1f} ms expected")
            prev_ts = ts
            if frames % 200 == 0:
                print(f"{frames} frames, {samples} samples, "
                      f"{gaps} gaps, last µV {data[-1]}")

        await pmd.stop_streaming('ECG')

asyncio.run(main())
