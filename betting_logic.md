### League of Legends Betting Logic

**Core Stat Types**:
- **Kills**: Number of enemy champions eliminated by a player
- **Assists**: Number of contributions to ally kills (non-lethal)
- **Combined K+A**: Often used for supports and team-oriented roles

**Map Scopes**:
- **Map 1 Only**: Highest variance; small sample size, higher volatility
- **Maps 1-2**: More stable; captures most best-of-three series outcomes
- **Series Total**: All maps played (1-3); influenced by game duration and sweep probability

**Role-Based Expectation**:
- **ADC/Mid**: High kills, moderate assists
- **Support**: Low kills, high assists
- **Jungle**: Balanced K+A, strong variance across patches
- **Top**: Lower K+A, less teamfight exposure

**Contextual Factors**:
- **Opponent Strength**: Weak teams concede more kills
- **Team Playstyle**: Aggressive teams inflate stats
- **Recent Form**: Influences z-score adjustments
- **Game Length**: Longer games = inflated stats

**Betting Considerations**:
- **Map 1**: Riskier bets, sharpest lines
- **Maps 1-2**: Better for model confidence and volatility smoothing
- **Avoid Overstacking Roles**: Correlation risk in parlays

**Model Strategy Tips**:
- Normalize all stats by minutes played
- Apply volatility penalties for small sample sizes
- Use tier-based weighting for players with limited historical data