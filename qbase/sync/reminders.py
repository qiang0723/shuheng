#!/usr/bin/env python3
"""到期台账提醒 · 只提醒不建议(施工清单第一日). root cron 每日. 到期/临期发飞书."""
import os, subprocess, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(HERE, "due_dates.conf")
today = datetime.date.today()
due = []

for raw in open(CFG, encoding="utf-8"):
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    parts = [p.strip() for p in line.split("|")]
    if len(parts) != 3:
        continue
    sched, lead_s, label = parts
    try:
        lead = int(lead_s)
    except ValueError:
        continue

    if sched.startswith("monthly-"):
        try:
            dd = int(sched.split("-", 1)[1])
        except ValueError:
            continue
        if today.day == dd:
            due.append((0, label, "每月"))
        continue

    target = None
    if len(sched) == 10 and sched[4] == "-":          # YYYY-MM-DD
        try:
            target = datetime.date.fromisoformat(sched)
        except ValueError:
            continue
    elif len(sched) == 5 and sched[2] == "-":         # MM-DD 每年
        try:
            m, d = map(int, sched.split("-"))
            target = datetime.date(today.year, m, d)
        except ValueError:
            continue
    if target is None:
        continue
    delta = (target - today).days
    if 0 <= delta <= lead:
        due.append((delta, label, target.isoformat()))

if due:
    lines = ["【枢衡·到期台账提醒】(只提醒不建议)"]
    for delta, label, when in sorted(due):
        tag = "今天到期" if delta == 0 else f"还有 {delta} 天"
        lines.append(f"  • {label} —— {when}({tag})")
    msg = "\n".join(lines)
    subprocess.run(["python3", os.path.join(HERE, "feishu_notify.py"), msg], check=False)
    print(msg)
else:
    print(f"{today} 无到期项")
