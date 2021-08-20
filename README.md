# LoLScrimAutomater
This code is meant to convert 1 folder of 1 game data (usually around +7000 individual JSON files) from https://bayesesports.com/ into a .csv file to input on a spreadsheet as per this document (https://docs.google.com/document/d/1d0nR6oXwWNZ8yDAfGge38dVE6TDg-QWhCjIQrr_7E8Y/edit?usp=sharing) (also down below)

It's really scrappy code since something was always different with the game data.
For any questions & concerns, feel free to hit me up on Discord xirimpi#3959.

### Objective
Automatically have an output of the following stats as seen in this sheet
This should be a quick and seamless process to save time for the team

### Labels
- Date of Game
- Game Number
- Opponent
- Winning team
    - 'winningteam' from <code>Match Subject</code> (100 for Team One, 200 for Team Two)

### General Matching
- Team Matching (Identify whether Blue or Red is CLG)
    - Which is 100 and which is 200?
- Player → Specific Stats
    - Ex. CLG Finn needs to be identified as the top laner</s>
    
### Objective Stats
- First Blood
	- Indicate which team obtained the first kill of the game
- First Drag
	- Indicate which team obtained first dragon of the game
- First Herald
	- Indicate which team obtained first herald of the game
- First tower
	- Indicate which team destroyed the first tower
- Mid Tower
	- Indicate which team took down the first tier 1 mid tower
        - Can be the same as first tower of game
        
### Individual Stats
- For each player, indicate the relative difference of the CLG player and the respective enemy player
    - [Top, Jungle, Mid, AD, Support]
    - CSD@10 - Creep Score Difference at 10 minutes
	- GD@10 - Gold Difference at 10 minutes 
        - <code>'currentgold'</code> from <code>Team One/Two</code> (for each player, but doesn't tell what lane is each player)
	- XPD@10 - Experience difference at 10 minutes
        - <code>'experience'</code> from <code>Team One/Two</code> (for each player, but doesn't tell what lane is each player
        - CSD@15 - Creep score difference at 15 minutes
        - XPD@15 - Experience difference at 15 minutes
    
### Team Stats
- Indicate the relative difference between CLG and the enemy team in…
	- GD@15 - Overall gold difference at 15 minutes
	- GD@20 - Overall gold difference at 20 minutes
    
### Bonus
- Isolated Deaths
    - Total count of deaths of a player when he’s isolated from the rest of the team

# How to use:
1) Download one of the 2 files here (I put 2 formats because I personally like iPython notebooks but there's also a straight Python file)
2) Download 1 game (folder of 7000 JSON files) from Bayes Esports
3) Copy directory address of game folder
4) Paste address into last function (scrim_automater) & run file
5) Save output as a .csv file
6) Open .csv file & copy & paste contents into Google Spreadsheet

# Things to change
1) The 2 objective functions, I use a player to identify which team - change the player to be someone from the current year's roster
