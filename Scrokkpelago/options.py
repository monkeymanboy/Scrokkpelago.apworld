from dataclasses import dataclass

from Options import (
    Toggle,
    Range,
    Choice,
    PerGameCommonOptions,
    DeathLink,
)

class CheckEveryCard(Toggle):
    """Using a card in a hand for the first time becomes a check."""
    display_name = "Check Every Card"
    default = 1

class PlusOneJoker(Toggle):
    """Adds a Joker item which acts as a spacer tile, allowing you to space out hands, to the item pool."""
    display_name = "Plus One Joker"
    default = 1

class ScoreThresholdCount(Range):
    """Number of score threshold checks to generate. Each score threshold is 500 points"""
    display_name = "Score Threshold Checks Count"
    range_start = 0
    range_end = 8
    default = 0

class CheckEveryHand(Toggle):
    """Adds a check for successfully completing each poker hand type."""
    display_name = "Check Every Hand "
    default = 1

class StartingTiles(Range):
    """Number of random unique cards given to the player at the start."""
    display_name = "Starting Tiles"
    range_start = 0
    range_end = 52
    default = 0

class Goal(Choice):
    """
    Determines the game's victory condition.

    Score:
        Reach the selected score threshold.

    Every Tile:
        Collect all 52 cards and use them all without busting.
    """
    display_name = "Goal"

    option_score = 0
    option_every_tile = 1

    default = option_every_tile

class GoalScore(Range):
    """
    Determines the score required for the Score goal.

    The value represents 500 points.
    For example, 8 means 4,000 points.
    """
    display_name = "Goal Score"
    range_start = 1
    range_end = 8
    default = 8
 
class TilesPerThresholdLogic(Range):
    """
    Determines how many tiles are needed in logic for each 500 point score threshold if using score thresholds.
    
    Setting this too low could create an impossible seed so do not change it if you're not sure.
    The logic does not guarantee that the tiles can be scored together so too low and it will have a good chance of creating something impossible.
    """
    display_name = "Goal Score"
    range_start = 1
    range_end = 52
    default = 15

class ClearBoardTrapWeight(Range):
    """Weight for Clear Board Trap items in the filler pool."""
    display_name = "Clear Board Trap Weight"
    range_start = 0
    range_end = 100
    default = 50

class ProgressionHintTokenWeight(Range):
    """Weight for Progression Hint Token items in the filler pool."""
    display_name = "Progression Hint Token Weight"
    range_start = 0
    range_end = 100
    default = 50

@dataclass
class ScrokkpelagoOptions(PerGameCommonOptions):
    check_every_card: CheckEveryCard
    plus_one_joker: PlusOneJoker
    score_threshold_count: ScoreThresholdCount
    check_every_hand: CheckEveryHand
    starting_tiles: StartingTiles
    tiles_per_threshold: TilesPerThresholdLogic
    clear_board_weight: ClearBoardTrapWeight
    progression_hint_weight: ProgressionHintTokenWeight
    goal: Goal
    goal_score: GoalScore
    death_link: DeathLink