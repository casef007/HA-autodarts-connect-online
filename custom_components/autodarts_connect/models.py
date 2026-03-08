"""Datenmodelle für Autodarts Connect Online."""

class MatchState:
    """Hält den aktuellen Status und die Logik eines Dart-Matches."""
    def __init__(self, board_id=None):
        self.board_id = board_id
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
        self.current_player_is_local = False
        self.raw_players = [] # Interner Speicher für die Spielerdaten

    # ==========================================
    # AUTOMATISIERUNGS-HELFER (SMARTE SENSOREN)
    # ==========================================
    @property
    def ready_to_throw(self):
        if not self.current_player_is_local or self.leg_finished or self.match_finished:
            return False
        if self.darts_left <= 0:
            return False
        if self.board_status in ["Takeout started", "Takeout finished"]:
            return False
        return True

    @property
    def checkout_possible(self):
        # FIX: Prüft nun, ob genug Darts für den vorgeschlagenen Checkout übrig sind!
        return (len(self.checkout_guide) > 0 
                and self.current_player_is_local 
                and not self.leg_finished 
                and self.darts_left >= len(self.checkout_guide))

    @property
    def takeout_needed(self):
        needs_pull = (self.darts_left == 0 or self.is_busted or self.leg_finished)
        not_pulled = self.board_status not in ["Takeout finished", "Manual reset", "Started"]
        return needs_pull and not_pulled

    @property
    def waiting_for_opponent(self):
        return not self.current_player_is_local and not self.match_finished

    @property
    def current_player_won_match_or_leg(self):
        if not self.current_player_is_local:
            return False
        current_name = self.get_player_name(self.current_player_idx)
        if self.match_finished and self.match_winner_name == current_name:
            return True
        if self.leg_finished and self.leg_winner_name == current_name:
            return True
        return False

    # ==========================================
    # DATEN-UPDATE LOGIK (Bulletproof Partial Updates)
    # ==========================================
    def update_from_state(self, state_data):
        if not isinstance(state_data, dict):
            return

        if "variant" in state_data: 
            self.variant = state_data["variant"]
        if "state" in state_data: 
            self.raw_state = state_data["state"]
            
        # 1. SPIELER & LOKAL-CHECK (Nur updaten, wenn explizit im Payload)
        if "players" in state_data:
            self.raw_players = state_data["players"]
            self.players = [p.get("name", "Unknown") for p in self.raw_players if isinstance(p, dict)]
            
        if "player" in state_data:
            self.current_player_idx = state_data["player"]
            
        # Lokal-Check führt er JEDES MAL aus, nutzt aber die sicher gespeicherten raw_players
        if isinstance(self.raw_players, list) and len(self.raw_players) > self.current_player_idx:
            p_data = self.raw_players[self.current_player_idx]
            if isinstance(p_data, dict):
                self.current_player_is_local = (p_data.get("boardId") == self.board_id)
            else:
                self.current_player_is_local = False
                
        # 2. SCORES & STATS
        if "scores" in state_data: 
            self.scores = state_data["scores"]
        if "stats" in state_data: 
            self.stats = state_data["stats"]
        
        if "gameScores" in state_data and not state_data.get("finished", False):
            self.points_left = state_data["gameScores"]
            
        if "state" in state_data:
            guide = self.raw_state.get("checkoutGuide", [])
            self.checkout_guide = [g.get("name") for g in guide if isinstance(g, dict)] if isinstance(guide, list) else []
            
        # 3. AKTUELLER WURF
        if "turnBusted" in state_data: 
            self.is_busted = state_data["turnBusted"]
        if "turnScore" in state_data: 
            self.turn_score = state_data["turnScore"]
            
        if "turns" in state_data:
            turns = state_data["turns"]
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
                
        # Darts Left wird basierend auf dem aktuellen Stand berechnet
        self.darts_left = 0 if (self.is_busted or state_data.get("finished", self.leg_finished)) else max(0, 3 - len(self.current_turn_throws))
        
        # 4. MATCH STATUS
        if "finished" in state_data: 
            self.leg_finished = state_data["finished"]
        if "gameFinished" in state_data: 
            self.match_finished = state_data["gameFinished"]
        
        if "winner" in state_data:
            w_idx = state_data["winner"]
            if self.leg_finished and isinstance(w_idx, int) and 0 <= w_idx < len(self.players):
                self.leg_winner_name = self.players[w_idx]
                if self.variant == "X01" and len(self.points_left) > w_idx:
                    self.points_left[w_idx] = 0
                    
        if "gameWinner" in state_data:
            gw_idx = state_data["gameWinner"]
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
