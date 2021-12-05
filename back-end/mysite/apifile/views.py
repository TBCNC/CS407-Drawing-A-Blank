import operator
from functools import reduce
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.response import Response
from . import grids
from django.http import JsonResponse
from .models import Event, EventBounds, Workout, WorkoutPoint, Grid, Player, Team
import datetime
from rest_framework.decorators import api_view
from django.contrib.auth.models import User
# for testing only
from django.views.decorators.csrf import csrf_exempt


# Create your views here.


# example query on data

# from .serializers import HeroSerializer
# from .models import Hero


# class HeroViewSet(viewsets.ModelViewSet):
#     queryset = Hero.objects.all().order_by('name')
#     serializer_class = HeroSerializer

class PlayerLocation(viewsets.ViewSet):

    # Not a full implementation, mostly for testing.
    # Instead of responding with the grids, it should replace the entries in the database with your player's colour.
    # Might need the user to send their current + previous location to calculate speed + path.
    def create(self, request):
        playerInfo = request.data
        coords = playerInfo["coords"]
        colour = playerInfo["colour"]
        gridLoc = grids.latlong_to_grid(coords)

        radius = 4  # calculate radius depending on speed

        allGrids = grids.grids_in_radius(gridLoc, radius)

        # update colour database.

        return Response(allGrids)


"""class PlayerPath(viewsets.ViewSet):
    
    {
    "current_coords": [52.286849 , -1.5329895],
    "old_coords": [52.285951 , -1.5329989],
    "colour":  "red",
    "time_elapsed": 18
    }
    

    def create(self, request):
        playerInfo = request.data
        current_coords = playerInfo["current_coords"]
        old_coords = playerInfo["old_coords"]
        colour = playerInfo["colour"]
        time_elapsed = playerInfo["time_elapsed"]

        current_grid = grids.latlong_to_grid(current_coords)
        old_grid = grids.latlong_to_grid(old_coords)
        speed = grids.calculate_speed(current_grid, old_grid, time_elapsed)
        radius = grids.calculate_radius(speed)  # calculate radius depending on speed

        allGrids = grids.all_grids_with_path(old_grid, current_grid, radius)

        # update colour database.

        return Response(allGrids)"""


class LatlongsOfGrid(viewsets.ViewSet):

    # GET request: parameter = a grid coordinate, responds with the 4 coordinates.
    # get 4 coordinates of a grid for testing:
    # http://127.0.0.1:8000/gridsCoords/?grid=SP3003376262 enter a grid reference and you should get 4 coordinates.
    def list(self, request):
        # need to get actual grid + colour from database.
        grid = request.query_params.get("grid")
        if grid is None:
            return Response("need a grid reference, try: http://127.0.0.1:8000/gridsCoords/?grid=SP3195365415", 400)

        coords = grids.bounds_of_grid(grid)
        color = "red"  # get colour data from database
        jsonString = [
            {
                "colour": color,
                "coords": coords
            }
        ]
        return Response(jsonString)

    # post - receiving 4 coordinates => respond with all grids visible.
    # function works but quite slow especially if the bounding box is big.
    def create(self, request):
        coords = request.data[0]
        bl = coords['bottom_left']
        br = coords['bottom_right']
        tr = coords['top_right']
        tl = coords['top_left']

        allGrids = grids.grids_visible([bl, br, tr, tl])
        return Response(allGrids)


# test view to add events to db
def add_events(_):
    ev1 = Event.objects.create(start=datetime.datetime.now(),
                               end=datetime.datetime.now() + datetime.timedelta(days=50))
    ev2 = Event.objects.create(start=datetime.datetime.now() - datetime.timedelta(days=20),
                               end=datetime.datetime.now() + datetime.timedelta(days=20))
    EventBounds.objects.create(event=ev1, easting=431890, northing=265592)
    EventBounds.objects.create(event=ev1, easting=431932, northing=265511)
    EventBounds.objects.create(event=ev1, easting=432360, northing=265781)
    EventBounds.objects.create(event=ev1, easting=432315, northing=265866)
    EventBounds.objects.create(event=ev2, easting=431258, northing=265593)
    EventBounds.objects.create(event=ev2, easting=430952, northing=265558)
    EventBounds.objects.create(event=ev2, easting=430986, northing=265463)
    EventBounds.objects.create(event=ev2, easting=431259, northing=265432)
    return Response("events added")


def current_events(_):
    ret_val = dict()
    events = Event.get_current_events()
    for event in events:
        bounds = event.get_bounds()
        for i in range(0, len(bounds)):
            bounds[i] = grids.grid_to_latlong(bounds[i])
        values = {
            'start': event.start,
            'end': event.end,
            'bounds': bounds
        }

        ret_val[event.id] = values

    return JsonResponse(ret_val)


@csrf_exempt
@api_view(["POST"])
def record_workout(request):
    if request.method == 'POST':
        data = request.data
        waypoints = data["coordinates"]
        start = data["start"][:-1]  # removes 'Z' in timestamp
        end = data["end"][:-1]
        workout_type = data["type"]
        uid = data["uid"]
        player = Player.objects.get(user__id=uid)

        # convert to seconds - look at what this is
        dur = datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M:%S.%f') - datetime.datetime.strptime(start, '%Y-%m-%dT'
                                                                                                          '%H:%M:%S.%f')

        cals = calc_calories(type, dur)

        workout = Workout.objects.create(player=player, duration=dur.total_seconds(), calories=cals, type=workout_type)

        for entry in waypoints:
            latlong = (entry["latitude"], entry["longitude"])
            easting, northing = grids.latlong_to_grid(latlong)
            timestamp = datetime.datetime.strptime(entry["timestamp"][:-1], '%Y-%m-%dT%H:%M:%S.%f')
            WorkoutPoint.objects.create(workout=workout, time=timestamp, easting=easting, northing=northing)

        bounds = WorkoutPoint.objects.filter(workout=workout).order_by('id')
        team = workout.player.team
        for i in range(1, len(bounds)):
            speed = grids.calculate_speed((bounds[i].easting, bounds[i].northing),
                                          (bounds[i - 1].easting, bounds[i - 1].northing),
                                          (bounds[i].time - bounds[i - 1].time).total_seconds())
            # calculate radius depending on speed
            radius = grids.calculate_radius(speed)
            allGrids = grids.all_grids_with_path((bounds[i].easting, bounds[i].northing),
                                                 (bounds[i - 1].easting, bounds[i - 1].northing), radius)
            tiles = Grid.objects.filter(reduce(operator.or_, (Q(easting=e, northing=n) for e, n in allGrids)))
            checkedTiles = []
            for tile in tiles:
                checkedTiles.append((tile.easting, tile.northing))
                if tile.check_tile_override(bounds[i].time):
                    tile.team = team
                    tile.time = bounds[i].time
                    tile.save()
            for tile in allGrids - checkedTiles:
                Grid.objects.create(easting=tile.easting, northing=tile.northing, team=team, time=bounds[i].time)

        return Response("workout added")


@csrf_exempt
@api_view(["POST"])
def create_user(request):
    if request.method == "POST":
        data = request.data
        name = data["name"]
        email = data["email"]
        pswd = data["pass"]
        user = User.objects.create_user(name, email, pswd)
        if len(Team.objects.all()) == 0:
            team = Team.objects.create(name="team1", colour="FF0000")
        else:
            team = Team.objects.get(name="team1")
        Player.objects.create(user=user, team=team)

        return Response("user added")


def calc_calories(workout_type, dur):
    return 0
