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
        self.vehicles_data = {}  # Dict indexed by vehicle ID
        self.vehicles_flags = {}  # Dict of flags indexed by vehicle ID

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

    async def get_vehicles_data(self):
        payload = self.build_payload("20101010", self.uid, self.ssk)
        seq = str(int(datetime.now().timestamp() * 1000))
        response = await asyncio.to_thread(
            requests.post, LOGIN_URL.format(seq=seq), headers=HEADERS,
            data=json.dumps(payload), verify=False
        )
        if response.ok:
            vehicles = response.json()["body"]["rows"]
            _LOGGER.info(f"✅ EVO-START: Found {len(vehicles)} vehicle(s)")
            return vehicles
        _LOGGER.error(f"❌ EVO-START: Failed to fetch vehicles data. Response: {response.text}")
        raise Exception("Failed to fetch vehicles data")

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

            vehicles = await self.get_vehicles_data()
            vehicles_data = {}
            vehicles_flags = {}
            
            for vehicle in vehicles:
                vehicle_id = vehicle["tid"]
                vst = vehicle["lloc"]["vst"]
                flags = self.decode_vst(vst)
                
                vehicles_data[vehicle_id] = {
                    "lloc": vehicle["lloc"],
                    "carinfo": vehicle.get("carinfo", {}),
                    "tid": vehicle["tid"]
                }
                vehicles_flags[vehicle_id] = flags
                
                _LOGGER.debug(f"📊 Vehicle {vehicle_id}: {vehicle.get('carinfo', {}).get('cname', 'Unknown')}")

            self.vehicles_data = vehicles_data
            self.vehicles_flags = vehicles_flags

            return {
                "vehicles": vehicles_data,
                "flags": vehicles_flags
            }
        except Exception as e:
            _LOGGER.exception("EVO-START: Error fetching data")
            raise UpdateFailed(str(e))

    async def async_remote_start(self, vehicle_id):
        if vehicle_id not in self.vehicles_data:
            _LOGGER.error(f"❌ Vehicle {vehicle_id} not found in vehicles_data")
            return False
        
        # Ensure we have valid authentication before sending command
        if not self.uid or not self.ssk:
            _LOGGER.warning("🔑 No valid authentication, attempting login...")
            if not await self.login():
                _LOGGER.error("❌ Failed to authenticate before remote start")
                return False
            
        payload = self.build_payload("303120", uid=self.uid, ssk=self.ssk, tid=vehicle_id)
        seq = str(int(datetime.now().timestamp() * 1000))
        
        _LOGGER.debug(f"🚗 Sending remote start command for vehicle {vehicle_id}")
        _LOGGER.debug(f"📦 Payload: {payload}")

        try:
            response = await asyncio.to_thread(
                requests.post,
                LOGIN_URL.format(seq=seq),
                headers=HEADERS,
                data=json.dumps(payload),
                verify=False
            )
            
            if not response.ok:
                _LOGGER.error(f"❌ HTTP error {response.status_code} for remote start: {response.text}")
                return False
                
            response_data = response.json()
            ret_code = response_data.get("sys_head", {}).get("ret_code")
            
            if ret_code == "000000":
                _LOGGER.info(f"🚗 Remote start triggered successfully for vehicle {vehicle_id}!")
                return True
            else:
                _LOGGER.error(f"❌ Remote start failed for vehicle {vehicle_id}. Return code: {ret_code}")
                _LOGGER.error(f"❌ Full response: {response.text}")
                return False
                
        except Exception as e:
            _LOGGER.exception(f"❌ Exception during remote start for vehicle {vehicle_id}: {e}")
            return False

    async def async_remote_stop(self, vehicle_id):
        if vehicle_id not in self.vehicles_data:
            _LOGGER.error(f"❌ Vehicle {vehicle_id} not found in vehicles_data")
            return False
        
        # Ensure we have valid authentication before sending command
        if not self.uid or not self.ssk:
            _LOGGER.warning("🔑 No valid authentication, attempting login...")
            if not await self.login():
                _LOGGER.error("❌ Failed to authenticate before remote stop")
                return False
            
        payload = self.build_payload("303125", uid=self.uid, ssk=self.ssk, tid=vehicle_id)
        seq = str(int(datetime.now().timestamp() * 1000))
        
        _LOGGER.debug(f"🛑 Sending remote stop command for vehicle {vehicle_id}")
        _LOGGER.debug(f"📦 Payload: {payload}")

        try:
            response = await asyncio.to_thread(
                requests.post,
                LOGIN_URL.format(seq=seq),
                headers=HEADERS,
                data=json.dumps(payload),
                verify=False
            )
            
            if not response.ok:
                _LOGGER.error(f"❌ HTTP error {response.status_code} for remote stop: {response.text}")
                return False
                
            response_data = response.json()
            ret_code = response_data.get("sys_head", {}).get("ret_code")
            
            if ret_code == "000000":
                _LOGGER.info(f"🛑 Remote stop triggered successfully for vehicle {vehicle_id}!")
                return True
            else:
                _LOGGER.error(f"❌ Remote stop failed for vehicle {vehicle_id}. Return code: {ret_code}")
                _LOGGER.error(f"❌ Full response: {response.text}")
                return False
                
        except Exception as e:
            _LOGGER.exception(f"❌ Exception during remote stop for vehicle {vehicle_id}: {e}")
            return False

    async def async_remote_lock(self, vehicle_id):
        if vehicle_id not in self.vehicles_data:
            _LOGGER.error(f"❌ Vehicle {vehicle_id} not found")
            return False
            
        payload = self.build_payload("303110", uid=self.uid, ssk=self.ssk, tid=vehicle_id)
        seq = str(int(datetime.now().timestamp() * 1000))

        response = await asyncio.to_thread(
            requests.post,
            LOGIN_URL.format(seq=seq),
            headers=HEADERS,
            data=json.dumps(payload),
            verify=False
        )
        if response.ok and response.json()["sys_head"]["ret_code"] == "000000":
            _LOGGER.info(f"🔒 Remote lock triggered successfully for vehicle {vehicle_id}!")
            return True
        else:
            _LOGGER.error(f"❌ Remote lock failed for vehicle {vehicle_id}. Response: {response.text}")
            return False

    async def async_remote_unlock(self, vehicle_id):
        if vehicle_id not in self.vehicles_data:
            _LOGGER.error(f"❌ Vehicle {vehicle_id} not found")
            return False
            
        payload = self.build_payload("303115", uid=self.uid, ssk=self.ssk, tid=vehicle_id)
        seq = str(int(datetime.now().timestamp() * 1000))

        response = await asyncio.to_thread(
            requests.post,
            LOGIN_URL.format(seq=seq),
            headers=HEADERS,
            data=json.dumps(payload),
            verify=False
        )
        if response.ok and response.json()["sys_head"]["ret_code"] == "000000":
            _LOGGER.info(f"🔓 Remote unlock triggered successfully for vehicle {vehicle_id}!")
            return True
        else:
            _LOGGER.error(f"❌ Remote unlock failed for vehicle {vehicle_id}. Response: {response.text}")
            return False

    def get_vehicle_data(self, vehicle_id):
        """Get data for a specific vehicle."""
        return self.vehicles_data.get(vehicle_id)
    
    def get_vehicle_flags(self, vehicle_id):
        """Get flags for a specific vehicle."""
        return self.vehicles_flags.get(vehicle_id, {})
    
    def get_all_vehicle_ids(self):
        """Get list of all vehicle IDs."""
        return list(self.vehicles_data.keys())
