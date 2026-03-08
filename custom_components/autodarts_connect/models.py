"""Datenmodelle für Autodarts Connect Online."""

class MatchState:
    """Hält den aktuellen Status und die Logik eines Dart-Matches."""
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
        self.current_player_is_local = False # Lokal oder Online

    # ==========================================
    # AUTOMATISIERUNGS-HELFER (SMARTE SENSOREN)
    # ==========================================
    @property
    def ready_to_throw(self):
        """True, wenn der lokale Spieler am Board steht und werfen darf."""
        if not self.current_player_is_local or self.leg_finished or self.match_finished:
            return False
        if self.darts_left <= 0:
            return False
        if self.board_status in ["Takeout started", "Takeout finished"]:
            return False
        return True

    @property
    def checkout_possible(self):
        """True, wenn der lokale Spieler mit den restlichen Darts das Leg beenden kann."""
        return (len(self.checkout_guide) > 0 
                and self.current_player_is_local 
                and not self.leg_finished 
                and self.darts_left > 0)

    @property
    def takeout_needed(self):
        """True, wenn Darts im Board stecken und gezogen werden müssen."""
        needs_pull = (self.darts_left == 0 or self.is_busted or self.leg_finished)
        not_pulled = self.board_status not in ["Takeout finished", "Manual reset", "Started"]
        return needs_pull and not_pulled

    @property
    def waiting_for_opponent(self):
        """True, wenn ein Online-Gegner oder Bot am Zug ist."""
        return not self.current_player_is_local and not self.match_finished

    # ==========================================
    # DATEN-UPDATE LOGIK
    # ==========================================
    def update_from_state(self, state_data):
        """Verarbeitet das .state JSON von Autodarts."""
        if not isinstance(state_data, dict):
            return

        self.variant = state_data.get("variant", self.variant)
        self.raw_state = state_data.get("state", {})
        
        if isinstance(state_data.get("players"), list):
            self.players = [p.get("name", "Unknown") for p in state_data["players"] if isinstance(p, dict)]
            
        if isinstance(state_data.get("player"), int):
            self.current_player_idx = state_data["player"]
            
        if isinstance(state_data.get("scores"), list):
            self.scores = state_data["scores"]
            
        if isinstance(state_data.get("stats"), list):
            self.stats = state_data["stats"]
        
        if isinstance(state_data.get("gameScores"), list) and not state_data.get("finished", False):
            self.points_left = state_data["gameScores"]
            
        guide = self.raw_state.get("checkoutGuide", [])
        self.checkout_guide = [g.get("name") for g in guide if isinstance(g, dict)] if isinstance(guide, list) else []
            
        self.is_busted = state_data.get("turnBusted", False)
        self.turn_score = state_data.get("turnScore", 0)
            
        turns = state_data.get("turns", [])
        if isinstance(turns, list) and len(turns) > 0:
            current_turn = turns[-1]
            if isinstance(current_turn, dict):
                throws = current_turn.get("throws", [])
                if isinstance(throws, list):
                    self.current_turn_throws = [t.get("segment", {}).get("name", "Miss") for t in throws if isinstance(t, dict)]
                if current_turn.get("busted", False):
                    self.is_busted = True
        else:
            self.current_turn_throws = []
            
        self.darts_left = 0 if (self.is_busted or state_data.get("finished", False)) else max(0, 3 - len(self.current_turn_throws))
        self.leg_finished = state_data.get("finished", False)
        self.match_finished = state_data.get("gameFinished", False)
        
        w_idx = state_data.get("winner", -1)
        if self.leg_finished and isinstance(w_idx, int) and 0 <= w_idx < len(self.players):
            self.leg_winner_name = self.players[w_idx]
            if self.variant == "X01" and len(self.points_left) > w_idx:
                self.points_left[w_idx] = 0
        
        gw_idx = state_data.get("gameWinner", -1)
        if self.match_finished and isinstance(gw_idx, int) and 0 <= gw_idx < len(self.players):
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
            if isinstance(s, dict):
                return round(s.get("average", 0), 2)
        return 0
