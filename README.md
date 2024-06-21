The goal of this repository to answer the questions: Given daily fantasy basketball projections, how likely are you to win your current 9cat matchup? How about your regular season, or your playoffs? What are the optimal actions you can take to improve those odds?

Note: this is beta! Not production level yet. 

The primary steps of this repo are:

1) Scrape/input daily stat projections to derive a weekly point estimate
2) Assign reasonable statistical distributions - using both statistical and basketball domain knowledge - to describe the uncertainty in those point estimates. 
3) Monte Carlo simulate the match-up to determine the probability of winning each statistical category, and the probability of each result (e.g 4-5, 6-3, etc)
4) Re-run to determine impact of benching players, or adding free agents. Use results to determine who to bench or who to drop.

Additionally, this idea is extended to project out the season given your exact schedule, everyone's current roster and record, and incorporates exact payout structure. This includes simulating the playoffs based on simulated regular season standings. This allows for exploring the impacts of trades and long-term FA pickups.

Finally, this repo includes some draft tools.
First is a simple linear programming optimization, useful for maximizing talent in an auction draft.

Second, and more importantly, this repo provides 'contextual rankings', which identify the rankings of players given your current roster (and the roster of all opponents). Generic rankings in fantasy are an approximation. A high-blocks player will be much more valuable to a average block team than to a team that already wins blocks by 30 every week. Being able to understand the contextual value of players helps you recognize ideal draft picks for your team (mid-draft!), identify high-value players that you can get for cheap, and identify win-win trades during the season.
