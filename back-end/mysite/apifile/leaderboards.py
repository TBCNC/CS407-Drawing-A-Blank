from django.db.models import Q

from . import stats
from .models import Workout, Player


def distance_leaderboard(time_range, teams):

    # Get all players/workouts from all teams
    if teams is None or teams == []:
        players = Player.objects.all()
        workouts = Workout.objects.filter(workoutpoint__time__gt=time_range).distinct()
    # Filter for teams in list.
    else:
        players = Player.objects.filter(team__name__in=teams)
        workouts = Workout.objects.filter(
            Q(workoutpoint__time__gt=time_range) & Q(player__team__name__in=teams)).distinct()

    # initialize the dictionary/hashmap.
    dist_leaderboard = {}
    for player in players:
        dist_leaderboard[player.user.username] = {"team": player.team.name, "score": 0.0}

    # go through all workouts.
    for workout in workouts:
        dist_leaderboard[workout.player.user.username]["score"] += stats.calc_workout_distance(workout)

    # sort distance dictionary
    sorted_dict = {k: v for k, v in sorted(dist_leaderboard.items(), key=lambda item: item[1]["score"], reverse=True)}

    # update format to an array of dicts.
    return_array = []
    for key, value in sorted_dict.items():
        return_array.append({"name": str(key), "team": value["team"], "score": value["score"]})
    return return_array
