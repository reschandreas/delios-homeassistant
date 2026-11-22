#!/usr/bin/env python3
"""Minimal client for the Delios inverter web API.

Usage:
    python delios_client.py --host http://<device-host> --user service --password service
"""
import argparse
import base64
import json
import time
import urllib.request
import urllib.error

DEFAULT_HOST = "http://delios.local"


class DeliosClient:
    def __init__(self, host=DEFAULT_HOST, username="service", password="service"):
        self.host = host.rstrip("/")
        self.username = username
        self.password = password
        self.token = None
        self.expire = 0
        self.level = None

    def login(self):
        req = urllib.request.Request(f"{self.host}/api/v1/token")
        req.add_header("Authorization", "Basic " + base64.b64encode(
            f"{self.username}:{self.password}".encode()).decode())
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.load(r)
        self.token = data["api_key"]
        self.expire = data["expire"]
        self.level = data["level"]
        return data

    def _ensure_token(self):
        if not self.token or time.time() >= self.expire - 60:
            self.login()

    def _get(self, path):
        self._ensure_token()
        req = urllib.request.Request(f"{self.host}{path}")
        req.add_header("x-access-token", self.token)
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.load(r)

    def _put(self, path, body):
        self._ensure_token()
        data = json.dumps(body).encode()
        req = urllib.request.Request(f"{self.host}{path}", data=data, method="PUT")
        req.add_header("x-access-token", self.token)
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.load(r)

    def refresh_token(self):
        self._ensure_token()
        req = urllib.request.Request(f"{self.host}/api/v1/token")
        req.add_header("x-access-token", self.token)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.load(r)
        self.token = data["api_key"]
        self.expire = data["expire"]
        self.level = data["level"]
        return data

    def change_password(self, new_password):
        return self._put("/api/v1/user/password", {"password": new_password})

    def dashboard(self): return self._get("/api/v1/dashboard")
    def status(self): return self._get("/api/v1/status")
    def alarms(self): return self._get("/api/v1/alarms")
    def info_system(self): return self._get("/api/v1/info/system")
    def info_totalizer(self): return self._get("/api/v1/info/totalizer")
    def info_firmware(self): return self._get("/api/v1/info/firmware")
    def system_status(self): return self._get("/api/v1/system/status")

    def chart(self, period, from_dt, to_dt):
        """period: 0 daily, 1 weekly, 2 yearly. from_dt/to_dt: datetime (naive, local)."""
        tzoff = time.timezone
        def jsts(d):
            return int((d.timestamp() * 1000 - tzoff * 1000) / 1000)
        return self._get(f"/api/v1/chart/{period}/{jsts(from_dt)}/{jsts(to_dt)}")

    @staticmethod
    def to_dict(resp):
        return resp


if __name__ == "__main__":
    import datetime
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--user", default="service")
    parser.add_argument("--password", default="service")
    args = parser.parse_args()
    c = DeliosClient(host=args.host, username=args.user, password=args.password)
    print("login:", c.login()["username"], "level", c.level)
    print("dashboard:", c.dashboard()["variables"][:3])
    print("totalizer:", c.info_totalizer())
    print("firmware:", c.info_firmware())
    print("system_status:", c.system_status())
    now = datetime.datetime.now()
    ch = c.chart(1, now - datetime.timedelta(days=7), now)
    print("chart weekly cats:", len(ch["categories"]), "sun[:3]:", ch["sunSerie"][:3])