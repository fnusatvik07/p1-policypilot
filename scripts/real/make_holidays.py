#!/usr/bin/env python
"""US federal holidays 2017-2027 from the `holidays` package (US federal calendar, observed rules).

Columns: date (the day the holiday is observed / offices closed), name, observed (True when the date is a
weekday substitute for a holiday falling on a weekend), actual_date (the statutory calendar date),
weekday, federal_reserve_closed (Fed Banks closed that weekday; Saturday holidays are not moved to Friday).
"""
import csv
from pathlib import Path

import holidays

OUT = Path(__file__).resolve().parents[2] / "data" / "real" / "calendar"
OUT.mkdir(parents=True, exist_ok=True)
rows = []
for year in range(2017, 2028):
    obs = holidays.country_holidays("US", years=year, observed=True)
    raw = holidays.country_holidays("US", years=year, observed=False)
    for d, name in sorted(obs.items()):
        is_obs = "(observed)" in name.lower()
        base = name.replace(" (observed)", "").replace(" (Observed)", "")
        actual_date = d
        if is_obs:
            near = holidays.country_holidays("US", years=[year - 1, year, year + 1], observed=False)
            actual_date = min((k for k, v in near.items() if v == base), key=lambda k: abs((k - d).days))
        # Federal Reserve Banks do not close on the Friday before a Saturday holiday (they do close the
        # Monday after a Sunday holiday) -- relevant for Reg E/Reg CC "business day" counting.
        fed_closed = d.weekday() < 5 and not (is_obs and d.weekday() == 4)
        rows.append({"date": d.isoformat(), "name": base, "observed": is_obs, "actual_date": actual_date.isoformat(),
                     "weekday": d.strftime("%A"), "federal_reserve_closed": fed_closed})
with open(OUT / "us_federal_holidays.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(len(rows), "rows; holidays pkg version", holidays.__version__)
