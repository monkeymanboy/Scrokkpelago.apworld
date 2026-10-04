# Scrokkpelago

Scrokkpelago is a poker-based Archipelago game where you collect cards and create hands on a crossword like board. Complete checks by using collecting and using each tile for the first time and completing different types of hands.

to get started you will need to configure your yaml at 
https://scrokkle.io/ap/yaml

## YAML Options
### Starting Tiles
As you might have guessed this is how many tiles you start the game with. You will always be able to make at least one hand with your starting tiles.
### Check Every Card
Adds a check location for the first time you use each type of card tile
### Check Every Hand
Adds a check location for the first time you create each type of hands
### Add a Joker
Adds a joker tile which can make going for specific hands a little easier. The joker tile can be placed between hands to build off without connecting to an existing hand on the board.
### Clear Trap Weight
The clear board trap does exactly what you think it does, if death link is enabled this does not also send a death link to other players.
### Hint Token Weight
The progression hint tokens will hint a progression item (or filler/trap if none are left) that is somewhere in Scrokkle.
### Score Threshold Checks
You generally do not need these are there are enough locations already but this adds more for eaching score thresholds, each threshold 500 more than the last.
### Use Score Goal
Instead of using all the tiles, you can have the goal be reaching a score threshold allowing completion before finding all the tiles.
### Start with nothing
This will override the starting tiles option and make it 0. You will not be able to do anything in Scrokkle from the start without another slot finding you tiles. This can cause world generation to fail if not played alongside other games that can find the tiles.