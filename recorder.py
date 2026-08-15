import asyncio, sqlite3, struct, time, json
from bleak import BleakScanner, BleakClient
from bleakheart import PolarMeasurementData, HeartRate

DB = "/var/lib/h10box/sessions.db"

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS sessions (
  id INTEGER PRIMARY KEY, started_ns INTEGER, ended_ns INTEGER,
  device TEXT, frames INTEGER DEFAULT 0, samples INTEGER DEFAULT 0,
  gaps INTEGER DEFAULT 0, rowing_session_id INTEGER,
  link_method TEXT, note TEXT);
CREATE TABLE IF NOT EXISTS ecg_frames (
  session_id INTEGER, ts_ns INTEGER, n INTEGER, samples BLOB);
CREATE TABLE IF NOT EXISTS hr_frames (
  session_id INTEGER, ts_ns INTEGER, hr INTEGER, rr_ms TEXT);
CREATE INDEX IF NOT EXISTS ix_ecg ON ecg_frames(session_id, ts_ns);
CREATE INDEX IF NOT EXISTS ix_hr  ON hr_frames(session_id, ts_ns);
"""

FS_NOMINAL = 130.0

def open_db():
    db = sqlite3.connect(DB, isolation_level=None)
    db.executescript(SCHEMA)
    return db

def start_session(db, address):
    cur = db.execute(
        "INSERT INTO sessions (started_ns, device) VALUES (?, ?)",
        (time.time_ns(), address))
    return cur.lastrowid

async def drain_ecg(db, sid, q, state):
    prev = None
    while True:
        item = await q.get()
        if item is None:
            break
        _, ts, data = item
        blob = struct.pack(f"<{len(data)}i", *data)
        db.execute("INSERT INTO ecg_frames VALUES (?,?,?,?)",
                   (sid, ts, len(data), blob))
        if prev is not None:
            expected = len(data) / FS_NOMINAL * 1e9
            if abs((ts - prev) - expected) > 0.5 * expected:
                state["gaps"] += 1
        prev = ts
        state["frames"] += 1
        state["samples"] += len(data)
        state["last_ns"] = ts

async def drain_hr(db, sid, q):
    while True:
        item = await q.get()
        if item is None:
            break
        _, ts, (hr, rrlist), _ = item
        db.execute("INSERT INTO hr_frames VALUES (?,?,?,?)",
                   (sid, ts, hr, json.dumps(rrlist)))

async def main():
    db = open_db()
    state = {"frames": 0, "samples": 0, "gaps": 0, "last_ns": None}

    dev = await BleakScanner.find_device_by_filter(
        lambda d, ad: d.name and "Polar" in d.name, timeout=60)
    if dev is None:
        return

    ecg_q, hr_q = asyncio.Queue(), asyncio.Queue()
    async with BleakClient(dev) as client:
        sid = start_session(db, dev.address)
        print("session", sid)

        hr = HeartRate(client, queue=hr_q, unpack=False)
        pmd = PolarMeasurementData(client, ecg_queue=ecg_q)

        await hr.start_notify()
        err, msg, _ = await pmd.start_streaming('ECG')
        if err != 0:
            print("ECG start failed:", msg)
            return

        tasks = [asyncio.create_task(drain_ecg(db, sid, ecg_q, state)),
                 asyncio.create_task(drain_hr(db, sid, hr_q))]
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        finally:
            db.execute("""UPDATE sessions SET ended_ns=?, frames=?,
                          samples=?, gaps=? WHERE id=?""",
                       (time.time_ns(), state["frames"], state["samples"],
                        state["gaps"], sid))

asyncio.run(main())
