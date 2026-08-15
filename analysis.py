import sqlite3, numpy as np, neurokit2 as nk

db = sqlite3.connect("/var/lib/h10box/sessions.db")

def load_ecg(session_id):
    rows = db.execute("SELECT ts_ns, n, samples FROM ecg_frames "
                      "WHERE session_id=? ORDER BY ts_ns", (session_id,)).fetchall()
    total = sum(r[1] for r in rows)
    fs = (total - rows[0][1]) * 1e9 / (rows[-1][0] - rows[0][0])
    step = 1e9 / fs
    ts = np.concatenate([r[0] - step * np.arange(r[1] - 1, -1, -1) for r in rows])
    vals = np.concatenate([np.frombuffer(r[2], dtype='<i4') for r in rows])
    return ts, vals.astype(float), fs

ts, ecg, fs = load_ecg(1)
print(f"fs={fs:.3f} Hz, {len(ecg)} samples, {(ts[-1]-ts[0])/1e9:.1f} s")

clean = nk.ecg_clean(ecg, sampling_rate=fs)
peaks, info = nk.ecg_peaks(clean, sampling_rate=fs)
idx = info["ECG_R_Peaks"]
rr = np.diff(ts[idx]) / 1e6            # ms, from device clock

print(f"{len(idx)} beats, mean HR {60000/np.mean(rr):.1f}")
print(f"RR mean {np.mean(rr):.1f} ms, SD {np.std(rr):.1f}, "
      f"min {np.min(rr):.0f}, max {np.max(rr):.0f}")

quality = nk.ecg_quality(clean, rpeaks=idx, sampling_rate=fs)
print(f"quality mean {np.mean(quality):.3f}, "
      f"fraction below 0.8: {np.mean(quality < 0.8):.3f}")
