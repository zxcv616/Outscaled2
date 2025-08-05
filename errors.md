Compiled with problems:
×
ERROR in src/components/enhanced/steps/MatchDetailsStep.tsx:131:37
TS7006: Parameter 'playerWord' implicitly has an 'any' type.
    129 |             
    130 |             // Check if any significant word from player name matches team name
  > 131 |             return playerWords.some(playerWord => 
        |                                     ^^^^^^^^^^
    132 |               playerWord.length > 2 && // Ignore short words
    133 |               teamWords.some(teamWord => 
    134 |                 teamWord.length > 2 &&