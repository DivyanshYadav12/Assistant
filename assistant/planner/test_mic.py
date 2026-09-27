"""Quick mic test — speak for 3 seconds, shows peak levels per device."""
import numpy as np
import sounddevice as sd
import time

for dev_id in [1, 5, 9, 11]:
    try:
        info = sd.query_devices(dev_id)
        rate = int(info["default_samplerate"])
        name = info["name"]
        print(f"Device {dev_id}: {name} rate={rate}")
        print("  Speak now (3s)...")
        with sd.InputStream(samplerate=rate, channels=1, dtype="int16", device=dev_id) as stream:
            all_data = []
            start = time.monotonic()
            while time.monotonic() - start < 3.0:
                frame, _ = stream.read(rate // 10)
                all_data.append(frame[:, 0].copy())
        combined = np.concatenate(all_data)
        peak = int(np.max(np.abs(combined)))
        rms = float(np.sqrt(np.mean(combined.astype(np.float64) ** 2)))
        print(f"  peak={peak}/32767  rms={rms:.1f}")
        if peak < 1000:
            print("  WARNING: very quiet - mic may be muted or gain too low")
        print()
    except Exception as e:
        print(f"  ERROR: {e}")
        print()
