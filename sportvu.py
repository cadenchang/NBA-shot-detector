import csv
import json
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import math


DATA_INDEX = 5
BALL_DATA = 0
Z_INDEX = 4
X_INDEX = 2
Y_INDEX = 3
TEAM_ID_INDEX = 0
PLAYER_ID_INDEX = 1
MOMENTS = 2
RIGHT_BASKET_X = 88.75
LEFT_BASKET_X = 5.25
BASKET_Y = 25
MIN_QUALIFYING_HEIGHT = 10.5
MIN_QUALIFYING_DISTANCE = 3


# Read in the SportVU tracking data
sportvu = []
with open('0021500495.json', mode='r') as sportvu_json:
   sportvu = json.load(sportvu_json)


shot_times = np.array([])  # Between 0 and 2880
unscaled_shot_facts = np.array([]) 
shot_facts = np.array([])  # Scaled between 0 and 10


def calculate_distance(ball_x, ref_x, ball_y, ref_y, ball_z=0, ref_z=0):
   distance = math.sqrt(
       (ref_x - ball_x) ** 2 +
       (ref_y - ball_y) ** 2 +
       (ref_z - ball_z) ** 2
   )
   return distance


def get_avg_def_distance(moment):
   ball_z = moment[DATA_INDEX][BALL_DATA][Z_INDEX]
   ball_x = moment[DATA_INDEX][BALL_DATA][X_INDEX]
   ball_y = moment[DATA_INDEX][BALL_DATA][Y_INDEX]
   num_players = len(moment[DATA_INDEX]) - 1  # Subtract 1 for the ball
   pwb = 0 # player with ball
   for i in range(1, num_players + 1):  # Iterate over players
       player_x = moment[DATA_INDEX][i][X_INDEX]
       player_y = moment[DATA_INDEX][i][Y_INDEX]
       player_z = moment[DATA_INDEX][i][Z_INDEX]
       player_distance_to_ball = calculate_distance(
           ball_x, player_x,
           ball_y, player_y,
           ball_z, player_z
       )
       if player_distance_to_ball <= MIN_QUALIFYING_DISTANCE:
           pwb = i


   tot_distance = 0
   num_players = len(moment[DATA_INDEX]) - 1  # Subtract 1 for the ball
   for i in range(1, num_players + 1):  # Iterate over players
       if moment[DATA_INDEX][i][TEAM_ID_INDEX] == moment[DATA_INDEX][pwb][TEAM_ID_INDEX] or i == pwb: # check to make sure players are on different teams
           continue


       player_with_ball_x = moment[DATA_INDEX][pwb][X_INDEX]
       player_with_ball_y = moment[DATA_INDEX][pwb][Y_INDEX]


       player_x = moment[DATA_INDEX][i][X_INDEX]
       player_y = moment[DATA_INDEX][i][Y_INDEX]
       player_distance_to_def = calculate_distance(
           player_with_ball_x, player_x,
           player_with_ball_y, player_y,
       )
       tot_distance += player_distance_to_def
      
   tot_distance /= 5
   return tot_distance


def player_has_ball_check(moment):
   ball_z = moment[DATA_INDEX][BALL_DATA][Z_INDEX]
   ball_x = moment[DATA_INDEX][BALL_DATA][X_INDEX]
   ball_y = moment[DATA_INDEX][BALL_DATA][Y_INDEX]
   num_players = len(moment[DATA_INDEX]) - 1  # Subtract 1 for the ball
   for i in range(1, num_players + 1):  # Iterate over players
       player_x = moment[DATA_INDEX][i][X_INDEX]
       player_y = moment[DATA_INDEX][i][Y_INDEX]
       player_z = moment[DATA_INDEX][i][Z_INDEX]
       player_distance_to_ball = calculate_distance(
           ball_x, player_x,
           ball_y, player_y,
           ball_z, player_z
       )
       if player_distance_to_ball <= MIN_QUALIFYING_DISTANCE:
           return True


   return False


# Initialize flag to track if distance calculation has been performed for the current shot


prev_z = 0
unique_times = set()
ball_under_10 = True
shot_in_progress = False
prev_time = 0
prev_clock_time = 0

for i, event in enumerate(sportvu['events']):
   for j, moment in enumerate(event['moments']):
       ball_z = moment[DATA_INDEX][BALL_DATA][Z_INDEX]
       ball_x = moment[DATA_INDEX][BALL_DATA][X_INDEX]
       ball_y = moment[DATA_INDEX][BALL_DATA][Y_INDEX]


       if shot_in_progress and ball_z < 10:
           shot_in_progress = False
          
       quarter = moment[0]
       time_left = moment[2]
       second_of_game = ((quarter - 1) * 720) + (720 - time_left)


       if second_of_game < prev_time:
           continue


       cur_clock_time = moment[2]


       if ball_z >= 10 and not shot_in_progress:  # Check if ball is above 10 feet and distance not calculated yet
           basket_x = LEFT_BASKET_X if ball_x < 47 else RIGHT_BASKET_X
           basket_y = BASKET_Y
           ball_in_basket_bubble = calculate_distance(ball_x, basket_x, ball_y, basket_y) <= 5
           if ball_in_basket_bubble:  # Ball is within basket bubble
               shot_detected = False
               shot_in_progress = True
               k = i
               while k >= 0:
                   event_backwards = sportvu['events'][k]
                   l = j if k == i else len(event_backwards['moments']) - 1
                   while l >= 0:
                       moment_backwards = event_backwards['moments'][l]
                       if player_has_ball_check(moment_backwards):
                           if not moment_backwards[1] in unique_times:
                               unique_times.add(moment_backwards[1])
                               quarter = moment_backwards[0]
                               time_left_in_quarter = moment_backwards[2]
                               total_time = ((quarter - 1) * 720) + (720 - time_left_in_quarter)
                               mins_left = time_left_in_quarter / int(60)
                               seconds_left = time_left_in_quarter % int(60)
                               if not cur_clock_time == prev_clock_time:
                                   shot_times = np.append(shot_times, total_time)
                                   closest_defender = get_avg_def_distance(moment_backwards)
                                   unscaled_shot_facts = np.append(unscaled_shot_facts, closest_defender)
                               shot_detected = True
                               found_first_moment_of_shot = True  # Set flag to indicate distance calculated for this shot
                               k = -1
                               break
                       l -= 1
                   if shot_detected:
                       break
                   k -= 1
       prev_time = second_of_game
       prev_clock_time = cur_clock_time


max_distance = unscaled_shot_facts.max()
min_distance = unscaled_shot_facts.min()

for elem in unscaled_shot_facts:
    elem = (elem - min_distance) / (max_distance - min_distance)
    elem *= 10
    shot_facts = np.append(shot_facts, elem)


# This code creates the timeline display from the shot_times
# and shot_facts arrays.
# DO NOT MODIFY THIS CODE APART FROM THE SHOT FACT LABEL
fig, ax = plt.subplots(figsize=(12,3))
fig.canvas.manager.set_window_title('Shot Timeline')


plt.scatter(shot_times, np.full_like(shot_times, 0), marker='o', s=50, color='royalblue', edgecolors='black', zorder=3, label='shot')
plt.bar(shot_times, shot_facts, bottom=2, color='royalblue', edgecolor='black', width=5, label='shot fact') # <- This is the label you can modify


ax.spines['bottom'].set_position('zero')
ax.spines['top'].set_color('none')
ax.spines['right'].set_color('none')
ax.spines['left'].set_color('none')
ax.tick_params(axis='x', length=20)
ax.xaxis.set_major_locator(matplotlib.ticker.FixedLocator([0,720,1440,2160,2880]))
ax.set_yticks([])


_, xmax = ax.get_xlim()
ymin, ymax = ax.get_ylim()
ax.set_xlim(-15, xmax)
ax.set_ylim(ymin, ymax+5)
ax.text(xmax, 2, "time", ha='right', va='top', size=10)
plt.legend(ncol=5, loc='upper left')


plt.tight_layout()
plt.show()


#plt.savefig("Shot_Timeline.png")


