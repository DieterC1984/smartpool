import logging
import requests
import json
import os
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

DOMAIN = "smartpool"
SESSION_FILE = "/config/.smartpool_session.json"
POOL_URL = "https://owner.smartpoolcontrol.eu/pools/measurements/2664/"
SCAN_INTERVAL = timedelta(seconds=300)

# Alle individuele sensoren, inclusief lighting en deck
SENSOR_TYPES = {
    "ph": "pH",
    "rx": "RX",
    "water_temp": "Water Temp",
    "outside_temp": "Outside Temp",
    "pump": "Pump",
    "deck": "Deck",
    "lighting": "Lighting"
}

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up Smart Pool sensors"""
    username = config.get("username")
    password = config.get("password")
    if not username or not password:
        _LOGGER.error("Smart Pool: username en password ontbreken in configuration.yaml")
        return

    session = SmartPoolSession(username, password)

    # Maak individuele sensoren
    sensors = [SmartPoolSensor(session, key, name) for key, name in SENSOR_TYPES.items()]
    add_entities(sensors, True)

# --------------------------
# Shared session class
# --------------------------
class SmartPoolSession:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self._session = None
        self._data = {}
        self.update()  # eerste fetch

    @Throttle(SCAN_INTERVAL)
    def update(self):
        try:
            self._session = self.get_session()
            r = self._session.get(POOL_URL)
            if r.status_code != 200:
                _LOGGER.error("Kon pool data niet ophalen, status_code: %s", r.status_code)
                return

            soup = BeautifulSoup(r.text, "html.parser")

            # Parse waarden
            self._data = {
                "ph": float(soup.find("div", id="card_PH").find("a").text.strip()),
                "rx": float(soup.find("div", id="card_RX").find("a").text.strip()),
                "water_temp": float(soup.find("div", id="card_temperatures")
                                   .find_all("div", class_="h5 mb-0 font-weight-bold text-gray-800")[0]
                                   .text.replace("°C", "").strip()),
                "outside_temp": float(soup.find("div", id="card_temperatures")
                                      .find_all("div", class_="h5 mb-0 font-weight-bold text-gray-800")[1]
                                      .text.replace("°C", "").strip()),
                "pump": soup.find("div", id="card_pump").find("a").text.strip(),
                "deck": soup.find("div", id="card_deck").find("a").text.strip(),
                "lighting": "on" if "fa-toggle-on" in str(soup.find("div", id="lighting_status")) else "off",
                "last_update": datetime.now().isoformat()
            }
        except Exception as e:
            _LOGGER.error("Fout bij ophalen Smart Pool data: %s", e)

    def get_session(self):
        session = requests.Session()
        # load previous session
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r") as f:
                try:
                    data = json.load(f)
                    session.cookies.set("sessionid", data.get("sessionid"))
                    session.cookies.set("csrftoken", data.get("csrftoken"))
                    last_login = datetime.fromisoformat(data.get("last_login", "2000-01-01T00:00:00"))
                    if datetime.now() - last_login < timedelta(days=13):
                        return session
                except Exception as e:
                    _LOGGER.warning("Kon session niet laden: %s", e)
        # login
        r = session.get("https://owner.smartpoolcontrol.eu/login/")
        csrftoken = r.cookies.get("csrftoken")
        payload = {
            "username": self.username,
            "password": self.password,
            "csrfmiddlewaretoken": csrftoken
        }
        headers = {"Referer": "https://owner.smartpoolcontrol.eu/login/"}
        r = session.post("https://owner.smartpoolcontrol.eu/login/", data=payload, headers=headers)
        if r.status_code not in [200, 302]:
            raise Exception("Login mislukt!")

        # save session
        data = {
            "sessionid": session.cookies.get("sessionid"),
            "csrftoken": session.cookies.get("csrftoken"),
            "last_login": datetime.now().isoformat()
        }
        with open(SESSION_FILE, "w") as f:
            json.dump(data, f)

        return session

# --------------------------
# Sensor class
# --------------------------
class SmartPoolSensor(Entity):
    def __init__(self, session: SmartPoolSession, key, name):
        self.session = session
        self.key = key
        self._name = name
        self._state = None

    @property
    def name(self):
        return f"Smart Pool {self._name}"

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return {"last_update": self.session._data.get("last_update")}

    def update(self):
        self.session.update()
        self._state = self.session._data.get(self.key)