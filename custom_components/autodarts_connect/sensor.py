"""Sensor-Plattform für Autodarts Connect Online - Full Version."""
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, SENSOR_CURRENT_PLAYER, SENSOR_GAME_MODE, SENSOR_BOARD_STATUS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Sensoren basierend auf einem Config Entry einrichten."""
    coord = hass.data[DOMAIN][config_entry.entry_id]
    
    # 1. GLOBALE MATCH-SENSOREN
    entities = [
        AutodartsSensor(coord, SENSOR_GAME_MODE, "mdi:gamepad-variant", lambda d: d.variant),
        AutodartsSensor(coord, SENSOR_CURRENT_PLAYER, "mdi:account", lambda d: d.get_player_name(d.current_player_idx)),
        AutodartsSensor(coord, SENSOR_BOARD_STATUS, "mdi:target", lambda d: d.board_status),
        AutodartsSensor(coord, "Current Score", "mdi:scoreboard", lambda d: d.get_player_score(d.current_player_idx)),
        AutodartsSensor(coord, "Turn Score", "mdi:counter", lambda d: d.turn_score),
        AutodartsSensor(coord, "Darts Left", "mdi:numeric-3-circle", lambda d: d.darts_left),
    ]
    
    # 2. GRANULARE WURF- UND CHECKOUT-SENSOREN (Dart 1-3)
    for i in range(1, 4):
        entities.append(AutodartsThrowSensor(coord, i))
        entities.append(AutodartsCheckoutSensor(coord, i))
        
    # 3. SPIELER-SPEZIFISCHE SENSOREN (PLAYER 1-4)
    for i in range(1, 5):
        entities.append(AutodartsSensor(coord, f"Player {i} Name", "mdi:account", lambda d, x=i: d.get_player_name(x-1)))
        entities.append(AutodartsSensor(coord, f"Player {i} Score", "mdi:scoreboard", lambda d, x=i: d.get_player_score(x-1)))
        entities.append(AutodartsSensor(coord, f"Player {i} Average", "mdi:chart-line", lambda d, x=i: d.get_player_average(x-1)))
        
        # Cricket Marks pro Spieler (20, 19, 18, 17, 16, 15, Bull)
        targets = ["20", "19", "18", "17", "16", "15", "25"]
        for t in targets:
            label = "Bull" if t == "25" else t
            entities.append(AutodartsCricketMarkSensor(coord, i, t, label))
        
    async_add_entities(entities)

class AutodartsSensor(CoordinatorEntity, SensorEntity):
    """Ein generischer Sensor für Autodarts Werte."""
    def __init__(self, coordinator, name, icon, value_fn):
        super().__init__(coordinator)
        self._attr_name = f"Autodarts {name}"
        self._attr_icon = icon
        self._value_fn = value_fn
        self._attr_unique_id = f"{coordinator.board_id}_{name.lower().replace(' ', '_')}"

    @property
    def device_info(self): return self.coordinator.device_info
    
    @property
    def native_value(self): return self._value_fn(self.coordinator.data)

class AutodartsThrowSensor(CoordinatorEntity, SensorEntity):
    """Sensor für einen einzelnen Wurf (1, 2 oder 3)."""
    def __init__(self, coordinator, num):
        super().__init__(coordinator)
        self._num = num
        self._attr_name = f"Autodarts Throw {num}"
        self._attr_unique_id = f"{coordinator.board_id}_throw_{num}"
        self._attr_icon = "mdi:arrow-projectile"

    @property
    def device_info(self): return self.coordinator.device_info
    
    @property
    def native_value(self):
        throws = self.coordinator.data.current_turn_throws
        return throws[self._num-1] if len(throws) >= self._num else ""

class AutodartsCheckoutSensor(CoordinatorEntity, SensorEntity):
    """Sensor für einen einzelnen Checkout-Vorschlag (1, 2 oder 3)."""
    def __init__(self, coordinator, num):
        super().__init__(coordinator)
        self._num = num
        self._attr_name = f"Autodarts Checkout Dart {num}"
        self._attr_unique_id = f"{coordinator.board_id}_checkout_{num}"
        self._attr_icon = "mdi:lightbulb-on"

    @property
    def device_info(self): return self.coordinator.device_info
    
    @property
    def native_value(self):
        guide = self.coordinator.data.checkout_guide
        return guide[self._num-1] if len(guide) >= self._num else ""

class AutodartsCricketMarkSensor(CoordinatorEntity, SensorEntity):
    """Sensor für Cricket-Marks einer bestimmten Zahl pro Spieler."""
    def __init__(self, coordinator, player_num, target_segment, label):
        super().__init__(coordinator)
        self._player_idx = player_num - 1
        self._target = target_segment
        self._attr_name = f"Autodarts P{player_num} Mark {label}"
        self._attr_unique_id = f"{coordinator.board_id}_p{player_num}_mark_{target_segment}"
        self._attr_icon = "mdi:bullseye-arrow"

    @property
    def device_info(self): return self.coordinator.device_info

    @property
    def native_value(self):
        state_data = self.coordinator.data.raw_state
        segments = state_data.get("segments", {})
        player_marks = segments.get(self._target, [])
        if len(player_marks) > self._player_idx:
            return player_marks[self._player_idx]
        return 0