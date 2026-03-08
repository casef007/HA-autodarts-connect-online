"""API-Client für die Kommunikation mit den Autodarts-Servern."""
import asyncio
import aiohttp
import json
import os
import logging

from .const import URL_CREDENTIALS, URL_TOKEN, URL_REST_STATE

_LOGGER = logging.getLogger(__name__)

class AutodartsApiClient:
    """Verwaltet Authentifizierung und REST-Abfragen."""
    def __init__(self, hass, email, password, session: aiohttp.ClientSession):
        self.hass = hass
        self.email = email
        self.password = password
        self.session = session
        self.cache_file = hass.config.path(".autodarts_connect_creds.json")

    async def _fetch_client_credentials(self):
        """Holt die geheimen Client-Credentials vom Hilfs-Server oder aus dem Cache."""
        def _save_creds(path, data):
            with open(path, "w", encoding="utf-8") as f: json.dump(data, f)
        def _load_creds(path):
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f: return json.load(f)
            return None

        try:
            async with self.session.get(URL_CREDENTIALS, timeout=10) as resp:
                if resp.status == 200:
                    creds = await resp.json()
                    await self.hass.async_add_executor_job(_save_creds, self.cache_file, creds)
                    return creds.get("client_id"), creds.get("client_secret")
        except Exception as e:
            _LOGGER.warning("Cred-Server nicht erreichbar, nutze Cache: %s", e)
            
        creds = await self.hass.async_add_executor_job(_load_creds, self.cache_file)
        return (creds.get("client_id"), creds.get("client_secret")) if creds else (None, None)

    async def get_access_token(self):
        """Generiert ein frisches Bearer-Token für die WebSocket-Verbindung."""
        c_id, c_sec = await self._fetch_client_credentials()
        if not c_id: 
            return None
            
        data = {
            "client_id": c_id, 
            "client_secret": c_sec, 
            "grant_type": "password", 
            "username": self.email, 
            "password": self.password
        }
        try:
            async with self.session.post(URL_TOKEN, data=data, timeout=10) as resp:
                if resp.status == 200: 
                    return (await resp.json())["access_token"]
        except Exception as e:
            _LOGGER.error("Login Fehler bei Autodarts: %s", e)
        return None

    async def fetch_initial_match_state(self, match_id, token):
        """Holt den Status eines frisch gestarteten Matches via REST."""
        url = URL_REST_STATE.format(match_id)
        headers = {"Authorization": f"Bearer {token}"}
        
        # FIX: Retry-Logik! Die Autodarts REST-API hinkt dem WebSocket oft 1-2 Sekunden hinterher.
        for attempt in range(4):
            try:
                async with self.session.get(url, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        return await resp.json()
            except Exception as e:
                _LOGGER.debug("Initial State noch nicht bereit (Versuch %s): %s", attempt + 1, e)
            
            # 1 Sekunde warten und nochmal probieren
            await asyncio.sleep(1)
            
        _LOGGER.warning("Konnte initialen Match-State für %s nach 4 Versuchen nicht laden.", match_id)
        return None
