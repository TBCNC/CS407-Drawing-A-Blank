import operator
from functools import reduce
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.response import Response
from . import grids
from .models import Event, Workout, WorkoutPoint, Grid, Player, Team, EventBounds
import datetime
from rest_framework.decorators import action
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.serializers import AuthTokenSerializer
from . import authentication


class Events(viewsets.ViewSet):
    authentication_classes = [authentication.ExpTokenAuthentication]

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def create(self, request):
        data = request.data
        start = datetime.datetime.strptime(data['start_date'], '%d/%m/%Y')
        end = datetime.datetime.strptime(data['end_date'], '%d/%m/%Y')
        bounds = data['bounds']

        event = Event.objects.create(start=start, end=end)

        for bound in bounds:
            easting, northing = grids.latlong_to_grid(bound)
            EventBounds.objects.create(event=event, easting=easting, northing=northing)

        return Response("Event added", status=status.HTTP_201_CREATED)

    def list(self, _):
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

        return Response(ret_val, status=status.HTTP_200_OK)


class UserProfile(viewsets.ViewSet):
    authentication_classes = [authentication.ExpTokenAuthentication]

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def create(self, request):
        data = request.data
        username = data["username"]
        email = data["email"]
        password = data["password"]
        team = data["team"]

        if team != "terra" and team != "windy" and team != "ocean":
            return Response("Invalid team selected", status=status.HTTP_409_CONFLICT)
        if User.objects.filter(email=email).exists():
            return Response("User with that email already exists", status=status.HTTP_409_CONFLICT)
        elif User.objects.filter(username=username).exists():
            return Response("User with that username already exists", status=status.HTTP_409_CONFLICT)

        user = User.objects.create_user(username, email, password)

        default_team_colours = {'terra': 'FF8C91', 'windy': '82FF8A', 'ocean': '47C4FF'}
        team, _ = Team.objects.get_or_create(name=team, defaults={'colour': default_team_colours[team]})

        Player.objects.create(user=user, team=team)

        token, _ = Token.objects.get_or_create(user=user)

        return Response({'token': token.key}, status=status.HTTP_201_CREATED)

    @action(methods=['post'], detail=False)
    def change_details(self, request):
        data = request.data
        user = request.user

        player = Player.objects.get(user=user)

        if "first_name" in data:
            user.first_name = data["first_name"]
        if "last_name" in data:
            user.last_name = data["last_name"]
        user.save()

        if "date_of_birth" in data:
            player.date_of_birth = datetime.datetime.strptime(data["date_of_birth"], "%d/%m/%Y").date()
        if "gender" in data:
            player.gender = data["gender"]
        if "height" in data:
            player.height = float(data["height"])
        if "weight" in data:
            player.weight = float(data["weight"])
        player.save()

        return Response("User details updated", status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def change_pass(self, request):
        data = request.data
        user = request.user

        user.set_password(data["new_password"])

        return Response("Password changed", status=status.HTTP_200_OK)


class GridView(viewsets.ViewSet):
    authentication_classes = [authentication.ExpTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @action(methods=['post'], detail=False)
    def collect(self, request):
        data = request.data
        bl = data['bottom_left']
        tr = data['top_right']
        zoom = data['zoom']

        allGrids = grids.sub_sample((bl, tr), sub_dimension=zoom)
        return Response(allGrids, status=status.HTTP_200_OK)


class WorkoutSubmission(viewsets.ViewSet):
    authentication_classes = [authentication.ExpTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request):
        data = request.data
        user = request.user

        waypoints = data["coordinates"]
        start = data["start"][:-1]  # removes 'Z' in timestamp
        end = data["end"][:-1]
        workout_type = data["type"]

        player = Player.objects.get(user=user)

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
            if len(allGrids) > 0:
                tiles = Grid.objects.filter(reduce(operator.or_, (Q(easting=e, northing=n) for e, n in allGrids)))
            else:
                tiles = []
            checkedTiles = set()
            for tile in tiles:
                checkedTiles.add((tile.easting, tile.northing))
                if tile.check_tile_override(bounds[i].time):
                    tile.team = team
                    tile.time = bounds[i].time
                    tile.save()
            for tile in allGrids - checkedTiles:
                Grid.objects.create(easting=tile[0], northing=tile[1], team=team, time=bounds[i].time)

        return Response("Workout added", status=status.HTTP_201_CREATED)


def calc_calories(workout_type, dur):
    return 0

class ObtainExpAuthToken(ObtainAuthToken):
    serializer_class = AuthTokenSerializer

    @classmethod
    def get_extra_actions(cls):
        return []

    def post(self, request):
        # authenticates username + password
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            # get the user and their current token if exists, or make new one if not exist
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)

            # if token fetched, refresh expiry
            if not created:
                token.created = datetime.datetime.utcnow()
                token.save()
            
            return Response({'token': token.key})
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

obtain_exp_auth_token = ObtainExpAuthToken.as_view()