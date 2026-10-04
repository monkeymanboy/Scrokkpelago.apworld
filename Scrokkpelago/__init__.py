from typing import Dict

from BaseClasses import Region, Location, Item, ItemClassification
from worlds.AutoWorld import World, WebWorld
from worlds.generic.Rules import set_rule

from .options import ScrokkpelagoOptions

SUITS = [
    "Hearts",
    "Diamonds",
    "Clubs",
    "Spades",
]

RANKS = [
    "Ace",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "Jack",
    "Queen",
    "King",
]

RANK_VALUES = {
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "Jack": 11,
    "Queen": 12,
    "King": 13,
    "Ace": 14,
}

HAND_NAMES = [
    "One Pair",
    "Two Pair",
    "Three of a Kind",
    "Straight",
    "Flush",
    "Full House",
    "Four of a Kind",
    "Straight Flush",
    "Five of a Kind", #only possible with multiple decks which is not currently possible in scrokkpelago but might be in the future with certain yaml configs
    "Royal Flush"
]

class ScrokkpelagoWeb(WebWorld):
    theme = "cardboard"

class ScrokkpelagoWorld(World):
    game = "Scrokkpelago"

    web = ScrokkpelagoWeb()

    options_dataclass = ScrokkpelagoOptions
    options: ScrokkpelagoOptions
    
    item_name_to_id: Dict[str, int] = {
        **{
            f"{rank} of {suit}": 40000 + (r_idx * len(SUITS)) + s_idx 
            for r_idx, rank in enumerate(RANKS) 
            for s_idx, suit in enumerate(SUITS)
        },
        "Joker": 49999,
        "Clear Board Trap": 50000,
        "Progression Hint Token": 50001,
    }

    location_name_to_id: Dict[str, int] = {
        **{
            f"Use: {rank} of {suit}": 60000 + (r_idx * len(SUITS)) + s_idx 
            for r_idx, rank in enumerate(RANKS) 
            for s_idx, suit in enumerate(SUITS)
        },
        **{
            f"Score Threshold {i * 500} Points": 70000 + (i - 1) 
            for i in range(1, 8)
        },
        **{
            f"Execute Hand: {hand}": 80000 + i 
            for i, hand in enumerate(HAND_NAMES)
        }
    }

    def generate_early(self):
        starting_tiles = self.options.starting_tiles.value
        if self.options.start_with_nothing:
            starting_tiles = 0
        self.starting_card_names = []
        if starting_tiles >= 2:
            all_cards = [
                f"{rank} of {suit}"
                for rank in RANKS
                for suit in SUITS
            ]
            used_cards = set()
            def add_card(rank, suit):
                card_name = f"{rank} of {suit}"
                if card_name not in used_cards:
                    used_cards.add(card_name)
                    self.starting_card_names.append(card_name)
            # 2-4 tiles: guaranteed random pair
            if starting_tiles <= 4:
                rank = self.random.choice(RANKS)
                suits = self.random.sample(SUITS, 2)
        
                for suit in suits:
                    add_card(rank, suit)
            # 5+ tiles: pair, flush, or straight with equal probability
            else:
                pattern = self.random.choice(["pair", "flush", "straight"])
                if pattern == "pair":
                    rank = self.random.choice(RANKS)
                    suits = self.random.sample(SUITS, 2)
                    for suit in suits:
                        add_card(rank, suit)
                elif pattern == "flush":
                    suit = self.random.choice(SUITS)
                    ranks = self.random.sample(RANKS, 5)
                    for rank in ranks:
                        add_card(rank, suit)
                elif pattern == "straight":
                    sequences = [
                        {14, 2, 3, 4, 5},
                        {2, 3, 4, 5, 6},
                        {3, 4, 5, 6, 7},
                        {4, 5, 6, 7, 8},
                        {5, 6, 7, 8, 9},
                        {6, 7, 8, 9, 10},
                        {7, 8, 9, 10, 11},
                        {8, 9, 10, 11, 12},
                        {9, 10, 11, 12, 13},
                        {10, 11, 12, 13, 14},
                    ]
                    sequence = self.random.choice(sequences)
                    for rank_value in sequence:
                        rank = next(
                            rank_name
                            for rank_name, value in RANK_VALUES.items()
                            if value == rank_value
                        )
                        suit = self.random.choice(SUITS)
                        add_card(rank, suit)
        
            remaining_cards = [
                card for card in all_cards
                if card not in used_cards
            ]
            self.random.shuffle(remaining_cards)
            self.starting_card_names.extend(remaining_cards[:starting_tiles - len(self.starting_card_names)])
            for card_name in self.starting_card_names:
                self.multiworld.push_precollected(self.create_item(card_name))


    def create_regions(self):
        menu = Region("Menu", self.player, self.multiworld)
        board = Region("Card Table", self.player, self.multiworld)

        menu.connect(board)
        for name, location_id in self.location_name_to_id.items():
            if 60000 <= location_id < 70000:
                if not self.options.check_every_card.value:
                    continue
            elif 70000 <= location_id < 80000:
                threshold_index = (location_id - 70000) + 1
                if threshold_index > self.options.score_threshold_count.value:
                    continue
            elif 80000 <= location_id < 90000:
                if not self.options.check_every_hand.value or location_id == 80008: #5 of a kind not currently possible so also skip adding that location
                    continue
            board.locations.append(Location(self.player, name, location_id, board))
        self.multiworld.regions += [menu, board]

    def create_items(self):
        total_location_count = len(self.multiworld.get_unfilled_locations(self.player))
        items = []
        remaining_starting_cards = list(self.starting_card_names)
        
        for suit in SUITS:
            for rank in RANKS:
                name = f"{rank} of {suit}"
                if name in remaining_starting_cards:
                    remaining_starting_cards.remove(name)
                    continue
                items.append(self.create_item(name))

        if self.options.plus_one_joker.value:
            items.append(self.create_item("Joker"))
            
        clear_weight = self.options.clear_board_weight.value
        hint_token_weight = self.options.progression_hint_weight.value
        while len(items) < total_location_count:
            item_type = self.random.choices(["Progression Hint Token", "Clear Board Trap"], weights=[hint_token_weight, clear_weight], k=1)[0]
            items.append(self.create_item(item_type))

        self.multiworld.itempool += items

    def set_rules(self):
        if self.options.check_every_card.value:
            for suit in SUITS:
                for rank in RANKS:
                    location_name = f"Use: {rank} of {suit}"
                    location = self.multiworld.get_location(location_name,self.player)
                    self._set_card_logic(location,rank,suit)

        if self.options.check_every_hand.value:
            for hand in HAND_NAMES:
                if hand == "Five of a Kind":
                    continue
                location_name = f"Execute Hand: {hand}"
                location = self.multiworld.get_location(location_name, self.player)
                self._set_hand_logic(location, hand)

        if self.options.score_threshold_count.value > 0:
            card_names = [f"{rank} of {suit}" for suit in SUITS for rank in RANKS]
            for i in range(1, self.options.score_threshold_count.value):
                location_name = f"Score Threshold {i * 500} Points"
                location = self.multiworld.get_location(location_name, self.player)
                set_rule(location, lambda state, threshold=i*self.options.tiles_per_threshold.value: sum(state.has(card, self.player) for card in card_names) >= threshold)

        if self.options.goal.value == self.options.goal.option_score:
            self._set_score_goal()
        else:
            self._set_every_tile_goal()
            
    def fill_slot_data(self) -> dict:
        return {
            "goal": self.options.goal.value,
            "goal_score": self.options.goal_score.value * 500
        }

    def _set_score_goal(self):
        goal_score = self.options.goal_score.value * 500
        location_name = (f"Score Threshold {goal_score} Points")
        if location_name not in self.location_name_to_id:
            raise ValueError(
                f"Goal Score is {goal_score} points, but only "
                f"{self.options.score_threshold_count.value} "
                f"score thresholds were generated. "
                f"Increase Score Threshold Count."
            )
        goal_location = self.multiworld.get_location(location_name, self.player)
        self.multiworld.completion_condition[self.player] = lambda state, location=goal_location: state.can_reach(location)

    def _set_every_tile_goal(self):
        card_names = [
            f"{rank} of {suit}"
            for suit in SUITS
            for rank in RANKS
        ]
        self.multiworld.completion_condition[self.player] = lambda state, cards=card_names: all(state.has(card, self.player) for card in cards)

    def has_card(self, state, rank, suit):
        return state.has(f"{rank} of {suit}", self.player)

    def rank_count(self, state, rank):
        return sum(self.has_card(state,rank,suit) for suit in SUITS)

    def suit_count(self, state, suit):
        return sum(self.has_card(state,rank,suit) for rank in RANKS)

    def other_cards_of_rank(self, state, rank, excluded_suit):
        return sum(self.has_card(state, rank, suit) for suit in SUITS if suit != excluded_suit)

    def other_cards_of_suit(self, state, suit, excluded_rank):
        return sum(self.has_card(state, rank, suit) for rank in RANKS if rank != excluded_rank)

    def _set_card_logic(self, location, rank, suit):
        def rule(state):
            if not self.has_card(state, rank, suit):
                return False
            return (self._card_can_pair(state, rank, suit) or self._card_can_any_straight(state, rank, suit) or self._card_can_any_flush(state, rank, suit))
        set_rule(location, rule)

    def _card_can_pair(self, state, rank, suit):
        return self.other_cards_of_rank(state, rank, suit) >= 1

    def straight_sequences_containing(self, rank):
        value = RANK_VALUES[rank]
        sequences = []
        # A-2-3-4-5
        if value in {14, 2, 3, 4, 5}:
            sequences.append({14, 2, 3, 4, 5})
        # 2-3-4-5-6 through 10-J-Q-K-A
        for start in range(2, 11):
            sequence = set(range(start, start + 5))
            if value in sequence:
                sequences.append(sequence)
        return sequences

    def _card_can_any_straight(self, state, rank, suit):
        card_value = RANK_VALUES[rank]

        for sequence in self.straight_sequences_containing(rank):
            possible = True
            for value in sequence:
                if value == card_value:
                    continue
                found = any(
                    self.has_card(state, other_rank, other_suit)
                    for other_rank in RANKS
                    if RANK_VALUES[other_rank] == value
                    for other_suit in SUITS
                )
                if not found:
                    possible = False
                    break
            if possible:
                return True
        return False

    def _card_can_any_flush(self, state, rank, suit):
        return self.other_cards_of_suit(state, suit, rank) >= 4

    def _set_hand_logic(self, location, hand):
        if hand == "One Pair":
            set_rule(location, lambda state: self._can_one_pair(state))
        elif hand == "Two Pair":
            set_rule(location, lambda state: self._can_two_pair(state))
        elif hand == "Three of a Kind":
            set_rule(location, lambda state: self._can_three_kind(state))
        elif hand == "Straight":
            set_rule(location, lambda state: self._can_straight(state))
        elif hand == "Flush":
            set_rule(location, lambda state: self._can_flush(state))
        elif hand == "Full House":
            set_rule(location, lambda state: self._can_full_house(state))
        elif hand == "Four of a Kind":
            set_rule(location, lambda state: self._can_four_kind(state))
        elif hand == "Straight Flush":
            set_rule(location, lambda state: self._can_straight_flush(state))
        elif hand == "Royal Flush":
            set_rule(location, lambda state: self._can_royal_flush(state))

    def _can_one_pair(self, state):
        return any(self.rank_count(state, rank) >= 2 for rank in RANKS)

    def _can_two_pair(self, state):
        pair_count = 0
        for rank in RANKS:
            if self.rank_count(state, rank) >= 2:
                pair_count += 1
        return pair_count >= 2

    def _can_three_kind(self, state):
        return any(self.rank_count(state, rank) >= 3 for rank in RANKS)

    def _can_straight(self, state):
        sequences = [
            {14, 2, 3, 4, 5},
            {2, 3, 4, 5, 6},
            {3, 4, 5, 6, 7},
            {4, 5, 6, 7, 8},
            {5, 6, 7, 8, 9},
            {6, 7, 8, 9, 10},
            {7, 8, 9, 10, 11},
            {8, 9, 10, 11, 12},
            {9, 10, 11, 12, 13},
            {10, 11, 12, 13, 14},
        ]
        for sequence in sequences:
            startingSuit = None
            isAllSameFlag = True
            # if you are wondering why this extra logic is necessary it's to make sure that royal and straight flushes do not count as regular flushes in logic
            for value in sequence:
                foundRank = False
                for rank in RANKS:
                    if RANK_VALUES[rank] != value:
                        continue
                    for suit in SUITS:
                        if not self.has_card(state, rank, suit):
                            continue
                        foundRank = True
                        if startingSuit is None:
                            startingSuit = suit
                        elif suit != startingSuit:
                            isAllSameFlag = False
                if not foundRank:
                    isAllSameFlag = False
                    break
            if foundRank and not isAllSameFlag:
                return True
        return False

    def _can_flush(self, state):
        sequences = [
            {14, 2, 3, 4, 5},
            {2, 3, 4, 5, 6},
            {3, 4, 5, 6, 7},
            {4, 5, 6, 7, 8},
            {5, 6, 7, 8, 9},
            {6, 7, 8, 9, 10},
            {7, 8, 9, 10, 11},
            {8, 9, 10, 11, 12},
            {9, 10, 11, 12, 13},
            {10, 11, 12, 13, 14},
        ]
    
        for suit in SUITS:
            suit_values = {
                RANK_VALUES[rank]
                for rank in RANKS
                if self.has_card(state, rank, suit)
            }
            if len(suit_values) >= 6:
                return True
            #the check is for a regular flush so royal or straight flush do not count
            if len(suit_values) == 5:
                if suit_values not in sequences:
                    return True
    
        return False
    
    def _can_full_house(self, state):
        for triple_rank in RANKS:
            if self.rank_count(state, triple_rank) < 3:
                continue
            for pair_rank in RANKS:
                if pair_rank == triple_rank:
                    continue
                if self.rank_count(state, pair_rank) >= 2:
                    return True
        return False

    def _can_four_kind(self, state):
        return any(self.rank_count(state, rank) >= 4 for rank in RANKS)

    def _can_straight_flush(self, state):
        sequences = [
            {14, 2, 3, 4, 5},
            {2, 3, 4, 5, 6},
            {3, 4, 5, 6, 7},
            {4, 5, 6, 7, 8},
            {5, 6, 7, 8, 9},
            {6, 7, 8, 9, 10},
            {7, 8, 9, 10, 11},
            {8, 9, 10, 11, 12},
            {9, 10, 11, 12, 13}
        ]
        for suit in SUITS:
            values = {
                RANK_VALUES[rank]
                for rank in RANKS
                if self.has_card(state, rank, suit)
            }
            for sequence in sequences:
                if sequence.issubset(values):
                    return True
        return False

    def _can_royal_flush(self, state):
        sequence = {10, 11, 12, 13, 14}
        for suit in SUITS:
            values = {
                RANK_VALUES[rank] for rank in RANKS if self.has_card(state, rank, suit)
            }
            if sequence.issubset(values):
                return True
        return False

    def get_filler_item_name(self):
        return "Progression Hint Token"

    def create_item(self, name: str):
        if name == "Joker" or name == "Progression Hint Token":
            classification = ItemClassification.filler
        elif name == "Clear Board Trap":
            classification = ItemClassification.trap
        else:
            classification = ItemClassification.progression

        return Item(name, classification, self.item_name_to_id[name], self.player)
