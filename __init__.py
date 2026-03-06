"""Die Autodarts Connect Online Integration."""
import asyncio
import aiohttp
import json
import logging
import os
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, URL_CREDENTIALS, URL_TOKEN, URL_WEBSOCKET, URL_REST_STATE

_LOGGER = logging.getLogger(__name__)

class MatchState:
    """Hält den aktuellen Status eines Dart-Matches."""
    def __init__(self):
        self.match_id = None
        self.variant = "Unknown"  
        self.players = []
        self.current_player_idx = 0
        self.points_left = []
        self.checkout_guide = []
        self.current_turn_throws = [] 
        self.board_status = "Idle"
        self.leg_finished = False
        self.match_finished = False
        self.leg_winner_name = None
        self.match_winner_name = None
        self.is_busted = False
        self.scores = []
        self.stats = []
        self.turn_score = 0
        self.darts_left = 3
        self.raw_state = {}

    def update_from_state(self, state_data):
        self.variant = state_data.get("variant", self.variant)
        self.raw_state = state_data.get("state", {})
        
        if "players" in state_data:
            self.players = [p.get("name", "Unknown") for p in state_data["players"]]
        if "player" in state_data:
            self.current_player_idx = state_data["player"]
        if "scores" in state_data:
            self.scores = state_data["scores"]
        if "stats" in state_data:
            self.stats = state_data["stats"]
        
        if "gameScores" in state_data and not state_data.get("finished", False):
            self.points_left = state_data["gameScores"]
            
        guide = self.raw_state.get("checkoutGuide", [])
        self.checkout_guide = [g.get("name") for g in guide] if guide else []
            
        self.is_busted = state_data.get("turnBusted", False)
        self.turn_score = state_data.get("turnScore", 0)
            
        turns = state_data.get("turns", [])
        if turns:
            current_turn = turns[-1]
            throws = current_turn.get("throws", [])
            self.current_turn_throws = [t.get("segment", {}).get("name", "Miss") for t in throws]
            if current_turn.get("busted", False):
                self.is_busted = True
        else:
            self.current_turn_throws = []
            
        self.darts_left = 0 if (self.is_busted or state_data.get("finished", False)) else max(0, 3 - len(self.current_turn_throws))
        self.leg_finished = state_data.get("finished", False)
        self.match_finished = state_data.get("gameFinished", False)
        
        w_idx = state_data.get("winner", -1)
        if self.leg_finished and 0 <= w_idx < len(self.players):
            self.leg_winner_name = self.players[w_idx]
            if self.variant == "X01" and len(self.points_left) > w_idx:
                self.points_left[w_idx] = 0
        
        gw_idx = state_data.get("gameWinner", -1)
        if self.match_finished and 0 <= gw_idx < len(self.players):
            self.match_winner_name = self.players[gw_idx]

    def get_player_name(self, idx):
        return self.players[idx] if len(self.players) > idx else "Unknown"

    def get_player_score(self, idx):
        if self.points_left and len(self.points_left) > idx:
            return self.points_left[idx]
        return 0

    def get_player_average(self, idx):
        if self.stats and len(self.stats) > idx:
            s = self.stats[idx].get("matchStats", {})
            return round(s.get("average", 0), 2)
        return 0


class AutodartsCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, email, password, board_id):
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=None)
        self.email = email
        self.password = password
        self.board_id = board_id
        self.data = MatchState()
        self.token = None
        self._websocket_task = None
        self.session = None
        self.cache_file = hass.config.path(".autodarts_connect_creds.json")

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.board_id)},
            name="Autodarts Board",
            manufacturer="Autodarts.io",
            model="Smart Board Online",
        )

    async def _async_update_data(self):
        return self.data

    async def async_start(self):
        self.session = aiohttp.ClientSession()
        # FIX 1: HA-Standard Task Creation
        self._websocket_task = self.hass.async_create_task(self._websocket_listener())

    async def async_stop(self):
        # FIX 2: Sauberer Cleanup mit Cancellation
        if self._websocket_task:
            self._websocket_task.cancel()
            try:
                await self._websocket_task
            except asyncio.CancelledError:
                pass
        if self.session:
            await self.session.close()

    async def _fetch_client_credentials(self):
        def _save_creds(path, data):
            with open(path, "w", encoding="utf-8") as f: json.dump(data, f)
        def _load_creds(path):
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f: return json.load(f)
            return None

        try:
            # Hier belassen wir timeout, da externe API
            async with self.session.get(URL_CREDENTIALS, timeout=10) as resp:
                if resp.status == 200:
                    creds = await resp.json()
                    await self.hass.async_add_executor_job(_save_creds, self.cache_file, creds)
                    return creds.get("client_id"), creds.get("client_secret")
        except Exception as e:
            _LOGGER.warning("Cred-Server nicht erreichbar, nutze Cache: %s", e)
            
        creds = await self.hass.async_add_executor_job(_load_creds, self.cache_file)
        return (creds.get("client_id"), creds.get("client_secret")) if creds else (None, None)

    async def _get_access_token(self):
        c_id, c_sec = await self._fetch_client_credentials()
        if not c_id: return None
        d = {"client_id": c_id, "client_secret": c_sec, "grant_type": "password", "username": self.email, "password": self.password}
        try:
            # FIX 3: ssl=False entfernt, da Autodarts gültige Zertifikate hat
            async with self.session.post(URL_TOKEN, data=d, timeout=10) as resp:
                if resp.status == 200: return (await resp.json())["access_token"]
        except Exception as e:
            _LOGGER.error("Login Fehler: %s", e)
        return None

    async def _fetch_initial_match_state(self, match_id):
        url = URL_REST_STATE.format(match_id)
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            # FIX 3: ssl=False entfernt
            async with self.session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    self.data.update_from_state(await resp.json())
                    self.async_set_updated_data(self.data)
        except Exception: pass

    async def _websocket_listener(self):
        while True:
            self.token = await self._get_access_token()
            if not self.token:
                self.last_update_success = False # FIX 4: Availability auf False
                self.async_update_listeners()
                await asyncio.sleep(30)
                continue
            
            try:
                # FIX 3: ssl=False entfernt
                async with self.session.ws_connect(URL_WEBSOCKET, headers={"Authorization": f"Bearer {self.token}"}, heartbeat=30) as ws:
                    _LOGGER.info("Autodarts WebSocket verbunden!")
                    self.last_update_success = True # FIX 4: Availability auf True
                    self.async_update_listeners()
                    
                    await ws.send_json({"channel": "autodarts.boards", "type": "subscribe", "topic": f"{self.board_id}.events"})
                    await ws.send_json({"channel": "autodarts.boards", "type": "subscribe", "topic": f"{self.board_id}.matches"})
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            payload = json.loads(msg.data)
                            channel, topic, data = payload.get("channel"), payload.get("topic", ""), payload.get("data", {})
                            
                            if channel == "autodarts.boards" and topic.endswith(".events"):
                                event = data.get("event")
                                if event == "Throw detected":
                                    seg = data.get("throw", {}).get("segment", {})
                                    self.hass.bus.async_fire("autodarts_throw", {
                                        "player": self.data.get_player_name(self.data.current_player_idx),
                                        "segment": seg.get("name", "Miss")
                                    })
                                    self.data.board_status = "Throwing"
                                    self.async_set_updated_data(self.data)
                                elif event in ["Takeout started", "Takeout finished", "Manual reset", "Started"]:
                                    self.data.board_status = event
                                    self.async_set_updated_data(self.data)

                            elif channel == "autodarts.boards" and topic.endswith(".matches"):
                                ev = data.get("event")
                                if ev == "start":
                                    self.data.match_id = data.get("id")
                                    self.hass.bus.async_fire("autodarts_match_started", {"board": self.board_id}) # NEUES EVENT
                                    await self._fetch_initial_match_state(self.data.match_id)
                                    await ws.send_json({"channel": "autodarts.matches", "type": "subscribe", "topic": f"{self.data.match_id}.state"})
                                elif ev == "delete" or ev == "finish":
                                    self.hass.bus.async_fire("autodarts_match_finished", {"board": self.board_id}) # NEUES EVENT
                                    self.data = MatchState()
                                    self.async_set_updated_data(self.data)

                            elif channel == "autodarts.matches" and topic.endswith(".state"):
                                old_finished = self.data.leg_finished
                                old_busted = self.data.is_busted
                                old_player = self.data.current_player_idx
                                
                                self.data.update_from_state(data)
                                
                                if self.data.current_player_idx != old_player:
                                    self.hass.bus.async_fire("autodarts_turn_started", {"player": self.data.get_player_name(self.data.current_player_idx)}) # NEUES EVENT
                                if self.data.leg_finished and not old_finished:
                                    self.hass.bus.async_fire("autodarts_leg_won", {"winner": self.data.leg_winner_name})
                                if self.data.is_busted and not old_busted:
                                    self.hass.bus.async_fire("autodarts_busted", {"player": self.data.get_player_name(self.data.current_player_idx)})
                                
                                self.async_set_updated_data(self.data)
                                
            except asyncio.CancelledError:
                raise
            except Exception as e:
                _LOGGER.error("WebSocket Fehler: %s. Reconnect...", e)
                self.last_update_success = False # FIX 4: Availability auf False
                self.async_update_listeners()
                await asyncio.sleep(5)


async def async_setup(hass, config):
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass, entry):
    coord = AutodartsCoordinator(hass, entry.data["email"], entry.data["password"], entry.data["board_id"])
    await coord.async_config_entry_first_refresh()
    await coord.async_start()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coord
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass, entry):
    # FIX 5: Der kritische Stop-Bug wurde hier mit await behoben!
    if unload_ok := await hass.config_entries.async_forward_entry_unload(entry, "sensor"):
        coord = hass.data[DOMAIN].pop(entry.entry_id)
        await coord.async_stop()
    return unload_ok