from datetime import timedelta, datetime
import asyncio
import hashlib
import json
import logging
import requests
import urllib3

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

LOGIN_URL = "https://shk.topm2m.net/webinv/do&req_seq={seq}"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest"
}

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BIT_FIELDS = {
    "lig_smal": 1,
    "lig_big": 2,
    "dor_frn": 3,
    "dor_trk": 4,
    "dor_rb": 5,
    "dor_rf": 6,
    "dor_lb": 7,
    "dor_lf": 8,
    "vcl_on2": 9,
    "vcl_on1": 10,
    "wnd_top": 12,
    "wnd_rb": 13,
    "wnd_rf": 14,
    "wnd_lb": 15,
    "vcl_anit": 16,
    "vcl_repair": 18,
    "vcl_lok": 19,
    "vcl_eng": 20,
    "vcl_acc": 21,
    "vcl_air": 22,
    "brk_fot": 23,
    "brk_han": 24,
    "gps_cls": 29,
    "gps_opn": 30,
    "gps_loc": 31,
    "gps_power": 32,
    "alm_tpms": 33,
    "alm_bat": 34,
    "alm_belt_m": 35,
    "alm_acc": 36,
    "alm_dor": 37,
    "alm_vib": 38,
    "alm_ultrasonic": 39,
    "alm_dor_open": 40
}

INVERTED_FLAGS = {"vcl_lok"}

FLAG_LABELS = {
    "vcl_lok": "central lock", "vcl_eng": "engine", "vcl_acc": "ACC", "dor_trk": "trunk",
    "lig_smal": "small lights", "lig_big": "headlights", "dor_frn": "hood", "dor_rb": "right back",
    "dor_rf": "right front", "dor_lb": "left rear", "dor_lf": "left front", "vcl_on2": "relay 2",
    "vcl_on1": "relay 1", "wnd_top": "sunroof", "wnd_rb": "right back window",
    "wnd_rf": "right front window", "wnd_lb": "left rear window", "vcl_anit": "anti-theft",
    "vcl_repair": "car repair", "vcl_air": "air conditioner", "brk_fot": "foot brake",
    "brk_han": "handbrake", "gps_cls": "GPS short circuit", "gps_opn": "GPS open circuit",
    "gps_loc": "GPS position", "gps_power": "GPS power", "alm_tpms": "tire pressure",
    "alm_bat": "low voltage", "alm_belt_m": "seat belt", "alm_acc": "illegal ignition",
    "alm_dor": "Illegal door opening", "alm_vib": "vibration", "alm_ultrasonic": "Ultrasound",
    "alm_dor_open": "Door not closed after locking"
}

OPEN_FLAGS = {
    "lig_smal", "lig_big", "dor_frn", "dor_rb", "dor_rf", "dor_lb", "dor_lf",
    "vcl_on2", "vcl_on1", "wnd_top", "wnd_rb", "wnd_rf", "wnd_lb", "vcl_anit",
    "vcl_repair", "vcl_air", "brk_fot", "brk_han", "gps_cls", "gps_opn",
    "gps_loc", "gps_power"
}

ALERT_FLAGS = {
    "alm_tpms", "alm_bat", "alm_belt_m", "alm_acc", "alm_dor",
    "alm_vib", "alm_ultrasonic", "alm_dor_open"
}

PRIORITY_FLAGS = ["vcl_lok", "vcl_eng", "vcl_acc", "dor_trk"]

class EvoStartCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, email, password):
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=60))
        self.email = email
        self.password = password
        self.uid = None
        self.ssk = None
        self.vehicle_data = None
        self.flags = {}

    def sha1_password(self, password: str) -> str:
        return hashlib.sha1(password.encode("utf-8")).hexdigest().upper()

    def build_payload(self, code: str, uid=None, ssk=None, tid=None):
        now = datetime.now()
        timestamp = str(int(now.timestamp()))
        return {
            "sys_head": {
                "code": code,
                "consumer_ssn": (uid or "00000000") + timestamp,
                "trans_date": now.strftime("%Y%m%d"),
                "trans_time": now.strftime("%H%M%S"),
                "build_make": "Home Assistant",
                "build_model": "Evo_Start Vehicle",
                "build_release": "1.0"
            },
            "app_head": {
                "ssk": ssk,
                "uid": uid or "00000000",
                "chnl": "web",
                "lang": "en"
            },
            "body": {} if not tid else {"tid": tid}
        }

    async def login(self):
        payload = self.build_payload("100010")
        payload["body"] = {"name": self.email, "paswd": self.sha1_password(self.password)}
        seq = str(int(datetime.now().timestamp() * 1000))
        try:
            response = await asyncio.to_thread(
                requests.post, LOGIN_URL.format(seq=seq), headers=HEADERS,
                data=json.dumps(payload), verify=False
            )
            if response.ok and response.json()["sys_head"]["ret_code"] == "000000":
                body = response.json()["body"]
                self.uid = body["uid"]
                self.ssk = body["ssk"]
                _LOGGER.info("✅ EVO-START: Login successful")
                return True
            _LOGGER.error(f"❌ EVO-START: Login failed. Response: {response.text}")
        except Exception:
            _LOGGER.exception("Exception during login")
        return False

    async def get_vehicle_data(self):
        payload = self.build_payload("20101010", self.uid, self.ssk)
        seq = str(int(datetime.now().timestamp() * 1000))
        response = await asyncio.to_thread(
            requests.post, LOGIN_URL.format(seq=seq), headers=HEADERS,
            data=json.dumps(payload), verify=False
        )
        if response.ok:
            return response.json()["body"]["rows"][0]
        _LOGGER.error(f"❌ EVO-START: Failed to fetch vehicle data. Response: {response.text}")
        raise Exception("Failed to fetch vehicle data")

    def decode_vst(self, vst: str):
        vst_cut = vst[:10]
        vst_bin = bin(int("1" + vst_cut, 16))[2:].zfill(41)
        _LOGGER.debug("📦 VST brut : %s", vst)
        _LOGGER.debug("📊 VST binaire : %s", vst_bin)

        flags = {}
        for key, idx in BIT_FIELDS.items():
            if idx >= len(vst_bin):
                flags[key] = None
            else:
                bit = vst_bin[idx]
                if key in INVERTED_FLAGS:
                    bit = "0" if bit == "1" else "1"
                flags[key] = bit

        def format_flag(k, v):
            label = FLAG_LABELS.get(k, k)
            if v not in ("0", "1"):
                return f"  - {k:12}: ❓ unknown ({label})"
            if k in OPEN_FLAGS:
                return f"  - {k:12}: {'🔴 open' if v == '1' else '🟢 close'} ({label})"
            elif k in ALERT_FLAGS:
                return f"  - {k:12}: {'⚠️ alert' if v == '1' else '✅ normal'} ({label})"
            else:
                return f"  - {k:12}: {'🔴 open' if v == '1' else '🟢 close'} ({label})"

        _LOGGER.debug("📋 Drapeaux interprétés (priorité) :\n%s", "\n".join(
            [format_flag(k, flags.get(k)) for k in PRIORITY_FLAGS]
        ))

        _LOGGER.debug("📋 Tous les autres drapeaux :\n%s", "\n".join(
            [format_flag(k, v) for k, v in flags.items() if k not in PRIORITY_FLAGS]
        ))

        return flags

    async def _async_update_data(self):
        try:
            _LOGGER.debug("🔄 EVO-START: Starting update")
            if not await self.login():
                raise UpdateFailed("Login failed")

            self.vehicle_data = await self.get_vehicle_data()
            vst = self.vehicle_data["lloc"]["vst"]
            self.flags = self.decode_vst(vst)

            return {
                "lloc": self.vehicle_data["lloc"],
                "carinfo": self.vehicle_data.get("carinfo", {}),
                "flags": self.flags
            }
        except Exception as e:
            _LOGGER.exception("EVO-START: Error fetching data")
            raise UpdateFailed(str(e))
