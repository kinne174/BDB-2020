import os
import matplotlib.pyplot as plt
import matplotlib.animation as animation

def main(params):
    gameId = params['gameId']
    playId = params['playId']

    fig = plt.figure()
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax = fig.add_subplot(111, xlim=(-10, 130), ylim=(-5, 58.3))
    ax.set_aspect(aspect='equal', adjustable='box')
    ax.set_title('gameId: {}, playId: {}'.format(str(gameId), str(playId)))

    Offense_positions, = ax.plot([], [], 'ro', ms=3)
    Defense_positions, = ax.plot([], [], 'go', ms=7)
    Football_position, = ax.plot([], [], 'mo', ms=5)

    Position_annotations = [
        ax.annotate(str(int(row['nflId']))[-3:], xy=(row['x'], row['y'])) if row['side'] == 'offense' else ax.annotate(
            '', xy=(row['x'], row['y'])) for _, row in
        tracking_df[(tracking_df['frame.id'] == 1) & (tracking_df['displayName'] != 'football')].iterrows()]
    for pa in Position_annotations:
        pa.set_animated(True)

if __name__ == '__main__':
    params = {
        'gameId': '',
        'playId': '',

    }
    main(params)
