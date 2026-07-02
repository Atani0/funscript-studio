from __future__ import annotations

from typing import Dict, List


def synthesize_actions(plan: List[Dict[str, object]], profile: Dict[str, object], duration_ms: int) -> List[Dict[str, int]]:
    amp_cfg = profile.get("amplitude", {}) if isinstance(profile, dict) else {}
    center = int(amp_cfg.get("center_pos", 50))
    min_pos = int(amp_cfg.get("min_pos", 8))
    max_pos = int(amp_cfg.get("max_pos", 92))
    actions: List[Dict[str, int]] = []
    direction = -1
    last_time = -10**9
    last_pos = center
    for index, item in enumerate(sorted(plan, key=lambda entry: int(entry["time"]))):
        time_ms = int(item["time"])
        if time_ms - last_time < 65:
            continue
        interval = time_ms - last_time if last_time > -1 else 999
        if interval > 520:
            direction *= -1
        elif interval < 170 and index % 3 != 0:
            direction = direction
        else:
            direction *= -1
        amplitude = float(item.get("amplitude", 40))
        wobble = ((index * 19) % 9 - 4)
        pos = round(center + direction * amplitude / 2 + wobble)
        pos = max(min_pos, min(max_pos, pos))
        if abs(pos - last_pos) < 4:
            pos = max(min_pos, min(max_pos, pos + (5 if direction > 0 else -5)))
        actions.append({"at": max(0, min(duration_ms, time_ms)), "pos": pos})
        last_time = time_ms
        last_pos = pos
    if not actions:
        return [{"at": 0, "pos": center}, {"at": max(1, duration_ms), "pos": center}]
    if actions[0]["at"] > 0:
        actions.insert(0, {"at": 0, "pos": center})
    gap_fill: List[Dict[str, int]] = [actions[0]]
    for prev, current in zip(actions, actions[1:]):
        if current["at"] - prev["at"] > 1200:
            mid = prev["at"] + (current["at"] - prev["at"]) // 2
            gap_fill.append({"at": mid, "pos": round((prev["pos"] + current["pos"]) / 2)})
        gap_fill.append(current)
    if gap_fill[-1]["at"] < duration_ms:
        gap_fill.append({"at": duration_ms, "pos": center})
    return dedupe_sort(gap_fill)


def dedupe_sort(actions: List[Dict[str, int]]) -> List[Dict[str, int]]:
    ordered = sorted(actions, key=lambda item: int(item["at"]))
    out: List[Dict[str, int]] = []
    for item in ordered:
        action = {"at": int(item["at"]), "pos": max(0, min(100, int(item["pos"])))}
        if out and out[-1]["at"] == action["at"]:
            out[-1] = action
        elif not out or abs(out[-1]["pos"] - action["pos"]) >= 2 or action["at"] - out[-1]["at"] > 700:
            out.append(action)
    return out
