"""DataUpdateCoordinator für Autodarts Connect Online."""
import asyncio
import aiohttp
import json
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, URL_WEBSOCKET
from .models import MatchState
from .api import AutodartsApiClient

_LOGGER = logging.getLogger(__name__)

class AutodartsCoordinator(DataUpdateCoordinator):
    """Verwaltet die WebSocket-Verbindung und verteilt die Daten an HA-Entitäten."""
    def __init__(self, hass, email, password, board_id):
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=None)
        self.board_id = board_id
        self.data = MatchState()
        self.session = None
        self.api = None
        self._websocket_task = None
        self._email = email
        self._password = password

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
        """Startet die HTTP Session und den WebSocket Task."""
        # HA Best-Practice Session Nutzung
        self.session = async_get_clientsession(self.hass)
        self.api = AutodartsApiClient(self.hass, self._email, self._password, self.session)
        
        # async_create_background_task verhindert, dass der HA-Start blockiert wird!
        self._websocket_task = self.hass.async_create_background_task(
            self._websocket_listener(),
            "autodarts_websocket_listener"
        )

    async def async_stop(self):
        """Beendet alle Verbindungen sauber beim Entladen."""
        if self._websocket_task:
            self._websocket_task.cancel()
            try:
                await self._websocket_task
            except asyncio.CancelledError:
                pass
        # Session darf hier NICHT geschlossen werden, da async_get_clientsession von HA verwaltet wird!

    async def _websocket_listener(self):
        """Der permanente Listener für die Autodarts Cloud."""
        while True:
            token = await self.api.get_access_token()
            if not token:
                self.last_update_success = False
                self.async_update_listeners()
                await asyncio.sleep(30)
                continue
            
            try:
                async with self.session.ws_connect(URL_WEBSOCKET, headers={"Authorization": f"Bearer {token}"}, heartbeat=30) as ws:
                    _LOGGER.info("Autodarts WebSocket verbunden!")
                    self.last_update_success = True
                    self.async_update_listeners()
                    
                    await ws.send_json({"channel": "autodarts.boards", "type": "subscribe", "topic": f"{self.board_id}.events"})
                    await ws.send_json({"channel": "autodarts.boards", "type": "subscribe", "topic": f"{self.board_id}.matches"})
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                # Defensives JSON-Parsing
                                payload = json.loads(msg.data)
                            except json.JSONDecodeError:
                                _LOGGER.debug("Ignoriere kaputte JSON-Payload vom Server: %s", msg.data)
                                continue
                                
                            channel = payload.get("channel")
                            topic = payload.get("topic", "")
                            data = payload.get("data", {})
                            
                            # 1. BOARD EVENTS
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

                            # 2. MATCH LEBENSZYKLUS
                            elif channel == "autodarts.boards" and topic.endswith(".matches"):
                                ev = data.get("event")
                                if ev == "start":
                                    self.data.match_id = data.get("id")
                                    self.hass.bus.async_fire("autodarts_match_started", {"board": self.board_id})
                                    
                                    initial_state = await self.api.fetch_initial_match_state(self.data.match_id, token)
                                    if initial_state:
                                        self.data.update_from_state(initial_state)
                                        
                                        # Prüfen, ob der Start-Spieler lokal ist!
                                        players = initial_state.get("players", [])
                                        if isinstance(players, list) and len(players) > self.data.current_player_idx:
                                            current_player_data = players[self.data.current_player_idx]
                                            if isinstance(current_player_data, dict):
                                                self.data.current_player_is_local = (current_player_data.get("boardId") == self.board_id)
                                            else:
                                                self.data.current_player_is_local = False
                                        else:
                                            self.data.current_player_is_local = False
                                            
                                        self.async_set_updated_data(self.data)
                                        
                                    await ws.send_json({"channel": "autodarts.matches", "type": "subscribe", "topic": f"{self.data.match_id}.state"})
                                elif ev == "delete" or ev == "finish":
                                    self.hass.bus.async_fire("autodarts_match_finished", {"board": self.board_id})
                                    self.data = MatchState()
                                    self.async_set_updated_data(self.data)

                            # 3. MATCH STATE UPDATES
                            elif channel == "autodarts.matches" and topic.endswith(".state"):
                                old_finished = self.data.leg_finished
                                old_busted = self.data.is_busted
                                old_player = self.data.current_player_idx
                                
                                self.data.update_from_state(data)
                                
                                # Prüfen, ob der aktuelle Spieler lokal ist
                                players = data.get("players", [])
                                if isinstance(players, list) and len(players) > self.data.current_player_idx:
                                    current_player_data = players[self.data.current_player_idx]
                                    if isinstance(current_player_data, dict):
                                        self.data.current_player_is_local = (current_player_data.get("boardId") == self.board_id)
                                    else:
                                        self.data.current_player_is_local = False
                                else:
                                    self.data.current_player_is_local = False
                                
                                if self.data.current_player_idx != old_player:
                                    self.hass.bus.async_fire("autodarts_turn_started", {
                                        "player": self.data.get_player_name(self.data.current_player_idx),
                                        "is_local": self.data.current_player_is_local
                                    })
                                if self.data.leg_finished and not old_finished:
                                    self.hass.bus.async_fire("autodarts_leg_won", {"winner": self.data.leg_winner_name})
                                if self.data.is_busted and not old_busted:
                                    self.hass.bus.async_fire("autodarts_busted", {"player": self.data.get_player_name(self.data.current_player_idx)})
                                
                                self.async_set_updated_data(self.data)
                                
            except asyncio.CancelledError:
                raise
            except Exception as e:
                _LOGGER.error("WebSocket Fehler: %s. Reconnect in 5 Sekunden...", e)
                self.last_update_success = False
                self.async_update_listeners()
                await asyncio.sleep(5)
