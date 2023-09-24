import matplotlib as mpl
import matplotlib.pyplot as plt

def create_rink(
    plot_half = True,
    board_radius = 25,
    alpha = 1,
):

    # Create a new figure
    fig, ax = plt.subplots(1, 1, figsize=(10, 12), facecolor='w', edgecolor='k')

    #Cornor Boards
    ax.add_artist(mpl.patches.Arc((100-board_radius , (85/2)-board_radius), board_radius * 2, board_radius * 2 , theta1=0, theta2=89, edgecolor='Black', lw=4.5,zorder=0, alpha = alpha)) #Top Right
    ax.add_artist(mpl.patches.Arc((-100+board_radius+.1 , (85/2)-board_radius), board_radius * 2, board_radius * 2 ,theta1=90, theta2=180, edgecolor='Black', lw=4.5,zorder=0, alpha = alpha)) #Top Left
    ax.add_artist(mpl.patches.Arc((-100+board_radius+.1 , -(85/2)+board_radius-.1), board_radius * 2, board_radius * 2 ,theta1=180, theta2=270, edgecolor='Black', lw=4.5,zorder=0, alpha = alpha)) #Bottom Left
    ax.add_artist(mpl.patches.Arc((100-board_radius , -(85/2)+board_radius-.1), board_radius * 2, board_radius * 2 ,theta1=270, theta2=360, edgecolor='Black', lw=4.5,zorder=0, alpha = alpha)) #Bottom Right

    #[x1,x2],[y1,y2]
    #Plot Boards
    ax.plot([-100+board_radius,100-board_radius], [-42.5, -42.5], linewidth=4.5, color="Black",zorder=0, alpha = alpha) #Bottom
    ax.plot([-100+board_radius-1,100-board_radius+1], [42.5, 42.5], linewidth=4.5, color="Black",zorder=0, alpha = alpha) #Top
    ax.plot([-100,-100], [-42.5+board_radius, 42.5-board_radius], linewidth=4.5, color="Black",zorder=0, alpha = alpha) #Left
    ax.plot([100,100], [-42.5+board_radius, 42.5-board_radius], linewidth=4.5, color="Black",zorder=0, alpha = alpha) #Right

    #Goal Lines
    adj_top = 4.6
    adj_bottom = 4.5
    ax.plot([89,89], [-42.5+adj_bottom, 42.5 - adj_top], linewidth=3, color="Red",zorder=0, alpha = alpha)
    ax.plot([-89,-89], [-42.5+adj_bottom, 42.5 - adj_top], linewidth=3, color="Red",zorder=0, alpha = alpha)

    #Plot Center Line
    ax.plot([0,0], [-42.5, 42.5], linewidth=3, color="Red",zorder=0, alpha = alpha)
    ax.plot(0,0, markersize = 6, color="Blue", marker = "o",zorder=0, alpha = alpha) #Center FaceOff Dots
    ax.add_artist(mpl.patches.Circle((0, 0), radius = 33/2, facecolor='none', edgecolor="Blue", linewidth=3,zorder=0, alpha = alpha)) #Center Circle

    #Zone Faceoff Dots
    ax.plot(69,22, markersize = 6, color="Red", marker = "o",zorder=0, alpha = alpha)
    ax.plot(69,-22, markersize = 6, color="Red", marker = "o",zorder=0, alpha = alpha)
    ax.plot(-69,22, markersize = 6, color="Red", marker = "o",zorder=0, alpha = alpha)
    ax.plot(-69,-22, markersize = 6, color="Red", marker = "o",zorder=0, alpha = alpha)

    #Zone Faceoff Circles
    ax.add_artist(mpl.patches.Circle((69, 22), radius = 15, facecolor='none', edgecolor="Red", linewidth=3,zorder=0, alpha = alpha))
    ax.add_artist(mpl.patches.Circle((69,-22), radius = 15, facecolor='none', edgecolor="Red", linewidth=3,zorder=0, alpha = alpha))
    ax.add_artist(mpl.patches.Circle((-69,22), radius = 15, facecolor='none', edgecolor="Red", linewidth=3,zorder=0, alpha = alpha))
    ax.add_artist(mpl.patches.Circle((-69,-22), radius = 15, facecolor='none', edgecolor="Red", linewidth=3,zorder=0, alpha = alpha))

    #Neutral Zone Faceoff Dots
    ax.plot(22,22, markersize = 6, color="Red", marker = "o",zorder=0, alpha = alpha)
    ax.plot(22,-22, markersize = 6, color="Red", marker = "o",zorder=0, alpha = alpha)
    ax.plot(-22,22, markersize = 6, color="Red", marker = "o",zorder=0, alpha = alpha)
    ax.plot(-22,-22, markersize = 6, color="Red", marker = "o",zorder=0, alpha = alpha)

    #Plot Blue Lines
    ax.plot([25,25], [-42.5, 42.5], linewidth=2, color="Blue",zorder=0, alpha = alpha)
    ax.plot([-25,-25], [-42.5, 42.5], linewidth=2, color="Blue",zorder=0, alpha = alpha)

    #Goalie Crease
    ax.add_artist(mpl.patches.Arc((89, 0), 6,6,theta1=90, theta2=270,  facecolor="Blue", edgecolor='Red', lw=2,zorder=0, alpha = alpha))
    ax.add_artist(mpl.patches.Arc((-89, 0), 6,6, theta1=270, theta2=90, facecolor="Blue", edgecolor='Red', lw=2,zorder=0, alpha = alpha))

    #Goal
    ax.add_artist(mpl.patches.Rectangle((89, 0 - (4/2)), 2, 4, lw=2, color='Red',fill=False,zorder=0, alpha = alpha))
    ax.add_artist(mpl.patches.Rectangle((-89 - 2, 0 - (4/2)), 2, 4, lw=2, color='Red',fill=False,zorder=0, alpha = alpha))

    if plot_half == False:
        # Set axis limits
        ax.set_xlim(-101, 101)
        ax.set_ylim(-43, 43)

    elif plot_half == True:
        # Set axis limits
        ax.set_xlim(-0.5, 100.5)
        ax.set_ylim(-43, 43)

    # Remove axis labels
    ax.set_xticklabels([])
    ax.set_yticklabels([])

    # Remove axis ticks
    ax.xaxis.set_ticks_position('none')
    ax.yaxis.set_ticks_position('none')

    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['top'].set_visible(False)

    return fig

if __name__ == '__main__':
    pass
