"""Check the actual loopback login, built assets and realtime frontend without site credentials."""

import json
import time
from html.parser import HTMLParser
from urllib.error import URLError
from urllib.request import urlopen

BASE = "http://127.0.0.1:18081"


class Assets(HTMLParser):
	def __init__(self):
		super().__init__()
		self.paths = set()

	def handle_starttag(self, tag, attrs):
		for name, value in attrs:
			if name in ("href", "src") and value and value.startswith("/assets/"):
				self.paths.add(value)


for attempt in range(30):
	try:
		with urlopen(BASE + "/login", timeout=5) as response:
			html = response.read().decode()
		break
	except URLError:
		if attempt == 29:
			raise
		time.sleep(1)
assets = Assets()
assets.feed(html)
if not assets.paths:
	raise SystemExit("Login page has no built application assets")
for path in sorted(assets.paths):
	with urlopen(BASE + path, timeout=5) as response:
		if response.status != 200:
			raise SystemExit("Application asset failed")
with urlopen(BASE + "/api/method/ping", timeout=5) as response:
	if json.load(response) != {"message": "pong"}:
		raise SystemExit("Framework ping failed")
with urlopen(BASE + "/socket.io/?EIO=4&transport=polling", timeout=5) as response:
	if not response.read().startswith(b"0{"):
		raise SystemExit("Realtime handshake failed")
print(f"PASS: login, {len(assets.paths)} built assets, ping and realtime handshake")
