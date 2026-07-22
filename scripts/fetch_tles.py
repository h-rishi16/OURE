import os
import sys

import requests

sys.path.append(os.path.abspath("."))
from oure.core.config import settings

print("Logging in to space-track...")
url = "https://www.space-track.org/ajaxauth/login"
data = {"identity": settings.spacetrack_user, "password": settings.spacetrack_pass}
s = requests.Session()
s.post(url, data=data)

print("Fetching 3LEs...")
# Fetch active satellites (EPOCH in last 3 days)
res = s.get(
    "https://www.space-track.org/basicspacedata/query/class/gp/EPOCH/>now-3/ORDERBY/NORAD_CAT_ID/FORMAT/3le"
)
with open("frontend/public/tles.txt", "w") as f:
    f.write(res.text)
print(f"Downloaded {len(res.text)} bytes.")
