import pandas as pd
import os
import datetime


def main(params):
    # this should all be done in the memory stick so assert that it exists
    # assert os.path.exists('D:/'), 'The memory stick is not detected.'

    # make sure that the original files are all there, probably won't mess with these
    assert os.path.exists(params['original_BDB_path']), 'Cannot find the data file in the memory stick.'
    assert all(os.path.exists(os.path.join(params['original_BDB_path'], f'week{i}.csv')) for i in range(1, 18)), 'Not all the weeks are detected.'
    assert os.path.exists(os.path.join(params['original_BDB_path'], 'games.csv')), 'The games csv is not found.'
    assert os.path.exists(os.path.join(params['original_BDB_path'], 'plays.csv')), 'The plays csv is not found.'
    assert os.path.exists(os.path.join(params['original_BDB_path'], 'players.csv')), 'The players csv is not found.'

    print('All original files found!')

    if os.path.exists(params['my_BDB_path']):
        assert params['overwrite_my_data'], 'You do not have "overwrite_my_data" set to True.'
        print('Overwriting files on your path: {}'.format(params['my_BDB_path']))

    else:
        print('Creating path {}'.format(params['my_BDB_path']))
        os.mkdir(params['my_BDB_path'])

    if params['by_games']:
        print('Creating unique game folders and unique .csv for each play')
        # for each game create a folder and within the folder create a .csv for each play, folder will be gameId and
        #  .csv will be playId (unique with the game)
        # will remove gameId and playId from columns

        by_games_path = os.path.join(params['my_BDB_path'], 'tracking_by_game')

        if not os.path.exists(by_games_path):
            os.mkdir(by_games_path)

        all_week_filenames = [os.path.join(params['original_BDB_path'], f'week{i}.csv') for i in range(1, 18)]
        for week, week_fn in enumerate(all_week_filenames):
            if week < 9:
                continue
            print("Starting Week {}: {}".format(week + 1, datetime.datetime.now()))
            week_df = pd.read_csv(week_fn)
            week_df.sort_values(by=['gameId', 'playId'], axis=0, inplace=True, ascending=True)

            # gameIds = week_df['gameId']
            # playIds = week_df['playId']
            # week_df.drop(['gameId', 'playId'], axis=1, inplace=True)
            #
            # i = 0
            # j = 0
            #
            # if not os.path.exists(os.path.join(by_games_path, str(gameIds[i]))):
            #     os.mkdir(os.path.join(by_games_path, str(gameIds[i])))
            # print('Next game: {}'.format(str(gameIds[i])))
            # print('Next play: {}'.format(str(playIds[i])))
            #
            # while True:
            #     if playIds[i] == playIds[j]:
            #         j += 1
            #
            #         if j >= len(playIds):
            #             out_df = week_df.iloc[i:, :]
            #             out_df.to_csv(os.path.join(by_games_path, str(gameIds[i]), '{}.csv'.format(str(playIds[i]))), index=False)
            #             break
            #     else:
            #         # print out to csv
            #         out_df = week_df.iloc[i:j, :]
            #         out_df.to_csv(os.path.join(by_games_path, str(gameIds[i]), '{}.csv'.format(str(playIds[i]))), index=False)
            #
            #         if not gameIds[i] == gameIds[j]:
            #             print('Next game: {}'.format(str(gameIds[j])))
            #             if not os.path.exists(os.path.join(by_games_path, str(gameIds[j]))):
            #                 os.makedirs(os.path.join(by_games_path, str(gameIds[j])))
            #
            #         print('Next play: {}'.format(str(playIds[j])))
            #         i = j

            unique_gameIds = set(week_df['gameId'].tolist())
            for gameId in unique_gameIds:
                print("Next game: {}".format(str(gameId)))
                if not os.path.exists(os.path.join(by_games_path, str(gameId))):
                    os.makedirs(os.path.join(by_games_path, str(gameId)))

                subset_df = week_df.loc[week_df['gameId'] == gameId]

                unique_playIds = set(subset_df['playId'].tolist())

                for playId in unique_playIds:
                    print("Next play: {}".format(playId))
                    output_df = subset_df.loc[subset_df['playId'] == playId]
                    output_df = output_df.drop(['gameId', 'playId'], axis=1)
                    output_df.to_csv(os.path.join(by_games_path, str(gameId), '{}.csv'.format(str(playId))), index=False)

        print('All done creating tracking by games! {}'.format(datetime.datetime.now()))


if __name__ == '__main__':
    params = {
        'original_BDB_path': 'D:/Football/BDB 2020/original_data/',
        'my_BDB_path': 'D:/Football/BDB 2020/my_data/',
        'overwrite_my_data': True,
        'by_games': True
    }
    main(params)
