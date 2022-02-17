from .models import Workout, Player
from . import grids
from django.db.models import Q

def distance_leaderboard(time_range,teams):
    # initialize the dictionary/hashmap.
    workouts = None
    players =None

    if(teams==None):
        players = Player.objects.all()
        workouts = Workout.objects.filter(workoutpoint__time__gt=time_range).distinct()
    else:
        players = Player.objects.filter(team__name__in=teams)
        workouts = Workout.objects.filter(Q(workoutpoint__time__gt=time_range) & Q(player__team__name__in=teams)).distinct()

    dist_leaderboard = {}
    for player in players:
        dist_leaderboard[player.user.username] = 0.0

    for workout in workouts:

        # get all the workoutpoints in the workout
        all_points = workout.workoutpoint_set.all()

        # calculate distance between each pair of adjacent points.
        cur_point = (all_points[0].easting, all_points[0].northing)
        dist = 0.0
        for point in all_points[1:]:
            dist += grids.distance(cur_point, (point.easting, point.northing))
            cur_point = (point.easting, point.northing)
        dist_leaderboard[workout.player.user.username] += dist

    # sort distance dictionary and return.
    return {k: v for k, v in sorted(dist_leaderboard.items(), key=lambda item: item[1], reverse=True)}
