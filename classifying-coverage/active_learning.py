import pandas as pd
import numpy as np
from shapely.geometry import LineString, Point
import matplotlib.pyplot as plt

from maintenance.load import load_play_by_game, all_playIds, all_gameIds
from plotting.active_learning_help import animate_play

# goal of this file is to build an svm that can classify a defender in man coverage or not man coverage
# since these are unlabeled I will need to calculate certain parameters about the play such as starting distance
# from line of scrimmage, average number of closest player, and distance run. These can be used to give an unsupervised
# approach at the begininng but with active learning I can label points as they appear to help the model learn on
# the fly. Labels will be appended to the play datasets, offensive players will have NA values. Should just be one column.
#
# Based on the number of players in man coverage, I will deduce the type of coverage and plot the projected area of
# coverage in a different file
#
# This is based on my previous work here: https://github.com/kinne174/BDB_revisit/blob/master/individual_coverage_active_learning.R

def main():
    global user_input
    # path to directory of tracking data by games
    tracking_data_folder = 'D:/Football/BDB_2020/my_data/tracking_by_game'

    # function to temporarily add in 'side' column for offense or defense
    def add_side_column(df):
        conditions = [
            (df['position'].isin(['QB', 'WR', 'RB', 'FB', 'TE'])),
            (df['position'].isin(['OLB', 'ILB', 'SS', 'FS', 'LB', 'CB'])),
            (df['position'].isnull()),
        ]

        values = ['offense', 'defense', 'football']

        df['side'] = np.select(conditions, values)

        return df

    # set up dictionary for models that will be used unsupervised and the svm for supervised

    # check to see if any models are available to load
    coverage_df = None
    classifier = None

    # glob gameIds
    gameIds = all_gameIds()

    # for loop over gameIds
    for gameId in gameIds:

        game_coverage_df = None

        # get all playIds
        playIds = all_playIds(gameId)

        # for loop over playIds
        for playId in playIds:
            play_df = load_play_by_game(gameId, playId)
            play_coverage_df = None

            # if coverage has been loaded in then continue
            if 'coverage' in play_df:
                continue

            # add side column to df
            play_df = add_side_column(play_df)

            # split between offense and defense
            offense_df = play_df[play_df['side'] == 'offense']
            defense_df = play_df[play_df['side'] == 'defense']

            # get linestrings of offense and defense players
            def create_linestring(player_df):
                return LineString([(x, y) for x, y in zip(player_df['x'], player_df['y'])])

            defense_ls = {}
            defense_nflIds = defense_df['nflId'].unique()
            for nflId in defense_nflIds:
                player_df = defense_df[defense_df['nflId'] == nflId]
                defense_ls[nflId] = create_linestring(player_df)

            offense_ls = {}
            offense_nflIds = offense_df['nflId'].unique()
            for nflId in offense_nflIds:
                player_df = offense_df[offense_df['nflId'] == nflId]
                offense_ls[nflId] = create_linestring(player_df)

            # get football los (x)
            footbal_los = play_df.loc[play_df['displayName'] == 'Football', 'x'].iloc[0]

            # for loop over each defensive player
            for dnflId, dls in defense_ls.items():

                # classify blitz
                blitz_frames = int(len(dls.coords)*.25)
                dls_xs, _ = dls.coords.xy[:blitz_frames]
                if all(x > footbal_los for x in dls_xs) or all(x < footbal_los for x in dls_xs):
                    coverage = None
                else:
                    coverage = 'blitz'

                # calculate number of unique offensive players they were closest to throughout the play
                def nearest_distance(p):
                    assert isinstance(p, Point)
                    min_distance = 1e9
                    min_nflId = None
                    for nflId, ls in offense_ls.items():
                        new_dist = p.distance(ls)
                        if new_dist < min_distance:
                            min_distance = new_dist
                            min_nflId = nflId
                    return (min_nflId, min_distance)

                min_nflIds, min_distances = map(list, zip(*[nearest_distance(Point(x, y)) for x, y in zip(*dls.coords.xy)]))
                num_closest_offense_players = len(set(min_nflIds))

                # calculate average distance they were from the closest offensive player
                average_closest_offense_distance = sum(min_distances) / len(min_distances)

                # calculate distance between their starting point and the line of scrimmage
                los_dist = abs(dls.coords.xy[0][0] - footbal_los)

                # calculate total distance they ran during the route
                total_distance = dls.length

                if coverage is None:
                    # predict coverage, if a classifier is present use it otherwise predict based on a rule
                    if classifier is not None:
                        raise NotImplementedError
                    else:
                        coverage = 'man' if (num_closest_offense_players <= 2 and los_dist <= 5) else 'zone'

                if play_coverage_df is None:
                    play_coverage_df = pd.DataFrame({'gameId': [gameId],
                                                     'playId': [playId],
                                                     'nflId': [dnflId],
                                                     'num closest': [num_closest_offense_players],
                                                     'avg closest': [average_closest_offense_distance],
                                                     'los distance': [los_dist],
                                                     'total distance': [total_distance],
                                                     'coverage': [coverage],
                                                     })
                    # play_coverage_df.set_index(keys='-'.join([gameId, playId, str(int(dnflId))]), inplace=True)
                else:
                    new_coverage_df = pd.DataFrame({'gameId': [gameId],
                                                     'playId': [playId],
                                                     'nflId': [dnflId],
                                                     'num closest': [num_closest_offense_players],
                                                     'avg closest': [average_closest_offense_distance],
                                                     'los distance': [los_dist],
                                                     'total distance': [total_distance],
                                                     'coverage': [coverage],
                                                     })
                    # new_coverage_df.set_index(keys='-'.join([gameId, playId, str(int(dnflId))]), inplace=True)
                    play_coverage_df = play_coverage_df.append(new_coverage_df, ignore_index=True)


            # based on calculations if model is trained can predict and plot for active learning, put prediction scores somewhere
            # change indices based on human input
            if classifier is not None:
                # only show plot if scores are not clear for changing
                raise NotImplementedError
            else:
                # show plot everytime for correction
                my_animation, fig = animate_play(params={'gameId': gameId,
                                                    'playId': playId,
                                                    'show': False,
                                                    'coverage_tuples': [(n, c) for n, c in zip(play_coverage_df['nflId'], play_coverage_df['coverage'])],
                                                    })

                def press(event):
                    global user_input
                    # print('press', event.key)
                    if event.key in [str(i) for i in list(range(10))]:
                        if int(event.key) not in user_input:
                            user_input.append(int(event.key))
                        print('Indices to change is {}'.format(', '.join([str(i) for i in user_input])))
                    if event.key in ['enter', 'q']:
                        plt.close()
                    if event.key in ['d']:
                        user_input = user_input[:-1]
                        print('Indices to change is {}'.format(', '.join([str(i) for i in user_input])))

                user_input = []
                fig.canvas.mpl_connect('key_press_event', press)

                plt.show()

                if user_input:
                    for i in user_input:
                        if play_coverage_df.iat[i, play_coverage_df.columns.get_loc('coverage')] == 'man':
                            play_coverage_df.iat[i, play_coverage_df.columns.get_loc('coverage')] = 'zone'
                        elif play_coverage_df.iat[i, play_coverage_df.columns.get_loc('coverage')] == 'zone':
                            play_coverage_df.iat[i, play_coverage_df.columns.get_loc('coverage')] = 'man'

            if game_coverage_df is None:
                game_coverage_df = play_coverage_df
            else:
                game_coverage_df = game_coverage_df.append(play_coverage_df, ignore_index=True)

        # after each game, labels have been updated do one step stochastic gradient descent update on svm
        if classifier is not None:
            # update classifier
            raise NotImplementedError
        else:
            # establish classifier
            raise NotImplementedError

        # predict on current game to see how well it is doing on training data


if __name__ == '__main__':
    main()