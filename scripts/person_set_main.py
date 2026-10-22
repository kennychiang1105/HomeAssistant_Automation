#!/usr/bin/env python3
"""Set the main device (device_trackers) of one family member in packages/persons.yaml.

Usage (run by shell_command.person_set_main inside the HA container):
    python3 /config/scripts/person_set_main.py <person_id> <device_tracker.entity_id> [label]

person.<id> is defined in YAML, so its tracker can only be changed by editing the file and calling person.reload.
The automation 00-2S (packages/v41_person_main_device.yaml) does the guard checks first and the reload afterwards.
Prints a single line: "OK ..." or "ERROR ...".  The previous file is kept as persons.yaml.bak.
"""
import os
import re
import shutil
import sys

PERSONS = "/config/packages/persons.yaml"
if not os.path.exists(PERSONS):
    PERSONS = "/homeassistant/packages/persons.yaml"
PIDS = ("kenny", "iris", "jerry", "elay")


def main():
    if len(sys.argv) < 3:
        print("ERROR usage: person_set_main.py <person_id> <device_tracker.entity> [label]")
        return 1
    pid, ent = sys.argv[1].strip(), sys.argv[2].strip()
    label = sys.argv[3].strip() if len(sys.argv) > 3 else ""
    if pid not in PIDS:
        print("ERROR unknown person %r" % pid)
        return 1
    if not re.fullmatch(r"device_tracker\.[a-z0-9_]+", ent):
        print("ERROR bad entity id %r" % ent)
        return 1
    text = open(PERSONS, encoding="utf-8").read()
    pat = re.compile(r"(^    id: %s\n    device_trackers:\n)((?:      (?:- |#).*\n)+)" % re.escape(pid), re.M)
    m = pat.search(text)
    if not m:
        print("ERROR person block %r not found" % pid)
        return 1
    note = "   # 主要裝置（自動化管理面板選擇%s）" % (("：" + label) if label else "")
    new_block = "      - %s%s\n" % (ent, note)
    if m.group(2) == new_block or m.group(2).split("#")[0].strip() == "- " + ent:
        print("OK unchanged %s -> %s" % (pid, ent))
        return 0
    new_text = text[:m.start(2)] + new_block + text[m.end(2):]
    try:
        import yaml
        d = yaml.safe_load(new_text)
        got = [p for p in d["person"] if p.get("id") == pid][0]["device_trackers"]
        if got != [ent]:
            print("ERROR validation failed: %r" % (got,))
            return 1
    except ImportError:
        pass
    shutil.copy(PERSONS, PERSONS + ".bak")
    tmp = PERSONS + ".tmp"
    open(tmp, "w", encoding="utf-8").write(new_text)
    os.replace(tmp, PERSONS)
    print("OK %s -> %s" % (pid, ent))
    return 0


if __name__ == "__main__":
    sys.exit(main())

