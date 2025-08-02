from app.utils.data_processor import DataProcessor

dp = DataProcessor()
lpl_data = dp.combined_data[(dp.combined_data['league'] == 'LPL') & (dp.combined_data['map_index_within_series'].between(1, 3))]

print('Teams for top LPL players:')
for player in ['Crisp', 'Rookie', 'Light', 'Xiaohu', '369']:
    player_data = lpl_data[lpl_data['playername'] == player]
    teams = list(player_data['teamname'].unique())
    print(f'{player}: {teams}') 