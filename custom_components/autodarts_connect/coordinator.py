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
        self.data = MatchState(self.board_id)
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
        self.session = async_get_clientsession(self.hass)
        self.api = AutodartsApiClient(self.hass, self._email, self._password, self.session)
        self._websocket_task = self.hass.async_create_background_task(
            self._websocket_listener(),
            "autodarts_websocket_listener"
        )

    async def async_stop(self):
        if self._websocket_task:
            self._websocket_task.cancel()
            try:
                await self._websocket_task
            except asyncio.CancelledError:
                pass

    async def _async_fetch_initial_state(self, match_id):
        """Hintergrund-Task: Lädt die Startdaten mit GARANTIERT frischem Token!"""
        # FIX: Zwingend ein frisches Token holen, da das WS-Token bei Folgematches abgelaufen ist!
        fresh_token = await self.api.get_access_token()
        if not fresh_token:
            _LOGGER.warning("Konnte kein frisches Token für Initial-State holen.")
            return

        initial_state = await self.api.fetch_initial_match_state(match_id, fresh_token)
        
        # Nur updaten, wenn wir noch im selben Match sind
        if initial_state and self.data.match_id == match_id:
            # SCHUTZ: Wenn der Spieler extrem schnell war und schon geworfen hat,
            # dürfen wir den echten Live-Status nicht mehr mit den REST-Startdaten überschreiben!
            if len(self.data.current_turn_throws) == 0 and self.data.turn_score == 0:
                self.data.update_from_state(initial_state)
                self.hass.bus.async_fire("autodarts_turn_started", {
                    "player": self.data.get_player_name(self.data.current_player_idx),
                    "is_local": self.data.current_player_is_local
                })
                self.async_set_updated_data(self.data)

    async def _websocket_listener(self):
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
                                payload = json.loads(msg.data)
                            except json.JSONDecodeError:
                                continue
                            
                            try:
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
                                        self.data = MatchState(self.board_id)
                                        self.data.match_id = data.get("id")
                                        self.hass.bus.async_fire("autodarts_match_started", {"board": self.board_id})
                                        
                                        # SOFORT subscriben!
                                        await ws.send_json({"channel": "autodarts.matches", "type": "subscribe", "topic": f"{self.data.match_id}.state"})
                                        
                                        # REST API im Hintergrund starten (ohne das alte Token zu übergeben!)
                                        self.hass.async_create_background_task(
                                            self._async_fetch_initial_state(self.data.match_id),
                                            f"autodarts_fetch_{self.data.match_id}"
                                        )
                                        
                                    elif ev == "delete":
                                        self.hass.bus.async_fire("autodarts_match_finished", {"board": self.board_id})
                                        self.data = MatchState(self.board_id)
                                        self.async_set_updated_data(self.data)
                                        
                                    elif ev == "finish":
                                        self.hass.bus.async_fire("autodarts_match_finished", {"board": self.board_id})

                                # 3. MATCH STATE UPDATES
                                elif channel == "autodarts.matches" and topic.endswith(".state"):
                                    old_finished = self.data.leg_finished
                                    old_busted = self.data.is_busted
                                    old_player = self.data.current_player_idx
                                    
                                    self.data.update_from_state(data)
                                    
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
                            except Exception as e:
                                _LOGGER.error("Interner Fehler bei der WS-Verarbeitung: %s", e)
                                
            except asyncio.CancelledError:
                raise
            except Exception as e:
                _LOGGER.error("WebSocket Fehler: %s. Reconnect in 5 Sekunden...", e)
                self.last_update_success = False
                self.async_update_listeners()
                await asyncio.sleep(5)
