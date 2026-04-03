# Fix: Light Not Changing Colors

## Problem
The breathing effect sends two separate UDP commands (`colorwc` + `brightness`) 20ms apart. The H607C drops one of these rapid commands, causing colors to never change.

## Fix

**File:** `govee/govee_lan_device.py` — `_breathe_thread` method (lines 225-310)

Revert to single-command approach: send one `colorwc` packet per tick with brightness baked into scaled RGB values.

### Changes:

1. Replace the two-command sequence (colorwc + brightness) with a single `colorwc` that scales RGB by `brightness / 100.0`

2. The key change in the loop body:

```python
# Map to brightness range
brightness = min_bright + (max_bright - min_bright) * gamma_eased
factor = brightness / 100.0

# Scale RGB by brightness factor and send as a single colorwc packet
scaled_r = max(1, int(round(r * factor)))
scaled_g = max(1, int(round(g * factor)))
scaled_b = max(1, int(round(b * factor)))

payload = {
    "msg": {
        "cmd": "colorwc",
        "data": {
            "color": {"r": scaled_r, "g": scaled_g, "b": scaled_b},
            "colorTemInKelvin": 0,
        },
    }
}
success = self._send_command_fast(payload)
```

3. Update docstring to reflect the single-command approach

### Trade-off
- **Pro:** Reliable — one atomic UDP command per tick, no race condition
- **Con:** Less deep dimming at the bottom of the exhale cycle (H607C has a minimum brightness floor when RGB values are very low), but colors will change consistently
