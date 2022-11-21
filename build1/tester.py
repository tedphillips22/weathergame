import random 

teams = [1, 2, 3, 4, 5, 6, 7, 8]
pairs = [(i, j) for i in teams for j in teams if i != j]
random.shuffle(pairs)

numWeeks = len(teams) - 1
numPairs = len(teams)//2
matchUps = {}
for week in range(numWeeks):
    matchUps[f'Week {week}'] = []
    for _ in range(numPairs):
        for pair in pairs:
            if pair[0] not in [team for match in matchUps[f'Week {week}'] for team in match]:
                if pair[1] not in [team for match in matchUps[f'Week {week}'] for team in match]:
                    if pair not in [match for w in range(week) for match in matchUps[f'Week {w}']] and (pair[1], pair[0]) not in [match for w in range(week) for match in matchUps[f'Week {w}']]:
                        break
        matchUps[f'Week {week}'].append(pair)

print(matchUps)