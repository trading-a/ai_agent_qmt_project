# -*- coding: utf-8 -*-
"""robot/config.py ? ?? config.yaml??? YAML ???????????"""
import os
import re

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")


def _parse_scalar(raw):
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1]
        items = []
        for part in _split_list(inner):
            items.append(_parse_scalar(part))
        return items
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]
    low = raw.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    if re.fullmatch(r"-?\d+\.\d+", raw):
        return float(raw)
    return raw


def _split_list(inner):
    out, buf, quote = [], [], None
    for ch in inner:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
            buf.append(ch)
        elif ch == ",":
            out.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        out.append("".join(buf).strip())
    return [b for b in out if b != ""]


def load_config(path=None):
    path = path or CONFIG_PATH
    cfg = {}
    section = None
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].rstrip()
            if not line.strip():
                continue
            if not line.startswith(" ") and line.strip().endswith(":"):
                section = line.strip()[:-1].strip()
                cfg[section] = {}
                continue
            m = re.match(r"^\s{2,}([A-Za-z0-9_]+):\s*(.*)$", line)
            if m and section:
                key, val = m.group(1), m.group(2)
                if val.strip() == "":
                    cfg[section][key] = {}
                else:
                    cfg[section][key] = _parse_scalar(val)
                continue
            # ???
            m2 = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
            if m2 and not section:
                cfg[m2.group(1)] = _parse_scalar(m2.group(2))
    return cfg


if __name__ == "__main__":
    import json
    print(json.dumps(load_config(), ensure_ascii=False, indent=2))
