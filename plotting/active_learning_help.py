import sys
sys.path.append("..")
from maintenance.load import load_play_by_game

import matplotlib; matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

# only difference between this and the other is this one will accept a coverage df to label the points

def animate_play(params={}):

    assert 'gameId' in params, 'GameId must be present to draw!'
    assert 'playId' in params, 'PlayId must be present to draw!'

    gameId = params['gameId']
    playId = params['playId']

    tracking_df = load_play_by_game(gameId, playId)

    conditions = [
        (tracking_df['position'].isin(['QB', 'WR', 'RB', 'FB', 'TE'])),
        (tracking_df['position'].isin(['OLB', 'ILB', 'SS', 'FS', 'LB', 'CB'])),
        (tracking_df['position'].isnull()),
    ]

    values = ['offense', 'defense', 'football']

    tracking_df['side'] = np.select(conditions, values)

    assert 'coverage_tuples' in params, 'Coverage tuples must be present to do active learning!'

    tracking_df['coverage'] = ''
    tracking_df['myid'] = -1
    for i, (nflId, cov) in enumerate(params['coverage_tuples']):
        tracking_df.loc[tracking_df['nflId'] == nflId, 'coverage'] = cov
        tracking_df.loc[tracking_df['nflId'] == nflId, 'myid'] = i

    fig = plt.figure()
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax = fig.add_subplot(111, xlim=(-10, 130), ylim=(-5, 58.3))
    ax.set_aspect(aspect='equal', adjustable='box')
    ax.set_title('gameId: {}, playId: {}'.format(str(gameId), str(playId)))

    Offense_positions, = ax.plot([], [], 'ro', ms=3)
    Defense_positions, = ax.plot([], [], 'go', ms=7)
    Football_position, = ax.plot([], [], color='cyan', marker='o', ms=5)

    Position_annotations = [
        ax.annotate('  {} - {}'.format(row['myid'], row['coverage']), xy=(row['x'], row['y'])) for _, row in
        tracking_df[(tracking_df['frameId'] == 1) & (tracking_df['side'] == 'defense')].iterrows()]
    for pa in Position_annotations:
        pa.set_animated(True)

    # draw field
    field = plt.Rectangle(xy=(0, 0), width=120, height=53.3, fill=False, lw=2)
    hash_lines = plt.Rectangle(xy=(10, 23.36667), width=100, height=6.6, fill=False, lw=1, linestyle='--')
    goal_lines = plt.Rectangle(xy=(10, 0), width=100, height=53.3, fill=False, lw=1)
    ax.add_patch(field)
    ax.add_patch(hash_lines)
    ax.add_patch(goal_lines)

    def _init_animate():

        Offense_positions.set_data([], [])
        Defense_positions.set_data([], [])
        Football_position.set_data([], [])
        field.set_edgecolor('none')
        hash_lines.set_edgecolor('none')
        goal_lines.set_edgecolor('none')
        for pa, ind_row in zip(Position_annotations, tracking_df[
            (tracking_df['frameId'] == 1) & (tracking_df['side'] == 'defense')].iterrows()):
            row = ind_row[1]
            pa.xy = (row['x'], row['y'])
            pa.set_position((row['x'], row['y']))

        return (
        Offense_positions, Defense_positions, Football_position, field, hash_lines, goal_lines, *Position_annotations)

    def _animate(i):

        i += 1
        Offense_positions.set_data(list(tracking_df['x'].loc[
                                            (tracking_df['side'] == 'offense') & (tracking_df['frameId'] == i) & (
                                                    tracking_df['displayName'] != 'Football')]), list(
            tracking_df['y'].loc[(tracking_df['side'] == 'offense') & (tracking_df['frameId'] == i) & (
                    tracking_df['displayName'] != 'Football')]))
        Defense_positions.set_data(list(tracking_df['x'].loc[
                                            (tracking_df['side'] == 'defense') & (tracking_df['frameId'] == i) & (
                                                    tracking_df['displayName'] != 'Football')]), list(
            tracking_df['y'].loc[(tracking_df['side'] == 'defense') & (tracking_df['frameId'] == i) & (
                    tracking_df['displayName'] != 'Football')]))
        Football_position.set_data(
            list(tracking_df['x'].loc[(tracking_df['frameId'] == i) & (tracking_df['displayName'] == 'Football')]),
            list(tracking_df['y'].loc[(tracking_df['frameId'] == i) & (tracking_df['displayName'] == 'Football')]))
        field.set_edgecolor('k')
        hash_lines.set_edgecolor('k')
        goal_lines.set_edgecolor('k')

        for pa, ind_row in zip(Position_annotations, tracking_df[
            (tracking_df['frameId'] == i) & (tracking_df['side'] == 'defense')].iterrows()):
            row = ind_row[1]
            pa.xy = (row['x'], row['y'])
            pa.set_position((row['x'], row['y']))

        return (
            Offense_positions, Defense_positions, Football_position, field, hash_lines, goal_lines,
            *Position_annotations)

    my_animation = animation.FuncAnimation(fig, _animate, frames=max(tracking_df['frameId']), interval=50,
                                  init_func=_init_animate, blit=True, repeat=True, repeat_delay=50)

    if params.get('show'):
        plt.show()
    else:
        return my_animation, fig