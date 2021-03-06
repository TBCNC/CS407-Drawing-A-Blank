import datetime
import math
import operator
from functools import reduce

import mahotas
import numpy as np
from django.contrib.auth.models import User
from django.db import models
from django.db.models import F, Q, Count
from django.db.models.functions import Cast
from shapely.geometry import Point, Polygon

from .constants import UNIT_TILE_SIZE


# 'python manage.py makemigrations' 'python manage.py migrate'
# run in terminal after changing/making new model, then register in admin.py


# stores conversions between easting/northing and lat/long for efficiency
class CoordsConvert(models.Model):
    easting = models.PositiveIntegerField()
    northing = models.PositiveIntegerField()
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        # ensure points are unique
        unique_together = (("easting", "northing"), ("latitude", "longitude"),)


# store team name and colour
class Team(models.Model):
    name = models.CharField(max_length=10, unique=True)
    colour = models.CharField(max_length=6)  # hex colour


# store items
class Item(models.Model):
    asset = models.FilePathField(path="items/asset")  # temp file paths
    thumbnail = models.FilePathField(path="items/thumbnail")  # temp file paths
    type = models.CharField(max_length=10)
    price = models.PositiveIntegerField()


# augment the base django user table with extra fields
class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField(null=True)
    gender = models.CharField(max_length=16, blank=True)
    height = models.FloatField(null=True)
    weight = models.FloatField(null=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    items = models.ManyToManyField(Item)
    coins = models.PositiveIntegerField(default=0)

    # calculate the number of points all users have scored since time
    @staticmethod
    def points(time, teams):

        # check if team filter is empty
        if teams is None or teams == []:
            teams = ['terra', 'windy', 'ocean']

        # filter workouts to ones from players in the team list and recorded since time
        workouts = Workout.objects.filter(
            date_recorded__gte=time, player__team__name__in=teams)

        # collect sum of points for each user
        points = {}
        for w in workouts:
            if w.player.user.username in points:
                points[w.player.user.username] += w.points
            else:
                points[w.player.user.username] = w.points

        # get all players of the respective teams
        all_players = Player.objects.values('user__username', 'team__name').filter(team__name__in=teams)

        ret_val = []
        # for each player return their name, team, and score
        for p in all_players:
            name = p["user__username"]
            team = p["team__name"]

            # retrieve a user's points if they have any
            if name in points:
                score = points[name]
            else:
                score = 0

            res = {"name": name,
                   "team": team,
                   "score": score}

            ret_val.append(res)

        return sorted(ret_val, key=lambda x: x["score"], reverse=True)


# store information about the map game state
class Grid(models.Model):
    easting = models.PositiveIntegerField()
    northing = models.PositiveIntegerField()
    time = models.DateTimeField()
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    published = models.BooleanField(default=False)

    # ensure only a single tile for each point can exist
    class Meta:
        unique_together = (("easting", "northing"),)

    # check if a timestamp is more recent than the current tile's time
    def check_tile_override(self, date_time):
        if self.time < date_time:
            return True
        else:
            return False


# store info about an event's structure
class Event(models.Model):
    start = models.DateTimeField()
    end = models.DateTimeField()
    players = models.ManyToManyField(Player, through='EventPerformance')
    active = models.BooleanField(default=False)

    # returns the closest event to a given point
    @staticmethod
    def get_closest_active_event(point):
        return Event.get_active_events().annotate(
            distance=((Cast(F('eventbounds__easting'), output_field=models.IntegerField())
                       - point[0]) ** 2
                      + (Cast(F('eventbounds__northing'), output_field=models.IntegerField())
                         - point[1]) ** 2)).order_by('distance').first()

    # returns the list of active events within a distance
    @staticmethod
    def get_events_within_distance(centre, dist):
        centre_easting, centre_northing = centre
        lower_easting = centre_easting - dist
        lower_northing = centre_northing - dist
        upper_easting = centre_easting + dist
        upper_northing = centre_northing + dist

        events = Event.get_active_events()
        events = events.filter(eventbounds__easting__gte=lower_easting,
                               eventbounds__northing__gte=lower_northing,
                               eventbounds__easting__lte=upper_easting,
                               eventbounds__northing__lte=upper_northing).distinct()

        closest_event = Event.get_closest_active_event(centre)
        if closest_event.check_within(centre):
            events = events.union(Event.objects.filter(id=closest_event.id))
        return events

    # gets events with a true active flag
    @staticmethod
    def get_active_events():
        curr_events = Event.objects.filter(active=True)

        return curr_events

    # open events that aren't active but start date has passed
    @staticmethod
    def open_events(date):
        to_start = Event.objects.filter(start__lte=date, end__gt=date, active=False)
        for event in to_start:
            # clear area
            event.clear_area()

            # switch flag
            event.active = True
            event.save()

    # close active events whose end date has passed
    @staticmethod
    def close_events(date):
        to_end = Event.objects.filter(end__lte=date, active=True)
        for event in to_end:
            # get winners
            winners = event.winner()
            unseen_teams = {"terra", "ocean", "windy"}
            teams = {"terra": Team.objects.get(name="terra"),
                     "ocean": Team.objects.get(name="ocean"),
                     "windy": Team.objects.get(name="windy")}

            # determine the place of each team
            if len(winners) >= 1:
                first = (teams[winners[0]['name']], winners[0]['total'])
                unseen_teams.remove(winners[0]['name'])
                if len(winners) >= 2:
                    second = (teams[winners[1]['name']], winners[1]['total'])
                    unseen_teams.remove(winners[1]['name'])
                    if len(winners) >= 3:
                        third = (teams[winners[2]['name']], winners[2]['total'])
                    else:
                        third = (teams[unseen_teams.pop()], 0)
                else:
                    second = (teams[unseen_teams.pop()], 0)
                    third = (teams[unseen_teams.pop()], 0)
            else:
                first = (teams[unseen_teams.pop()], 0)
                second = (teams[unseen_teams.pop()], 0)
                third = (teams[unseen_teams.pop()], 0)

            EventStandings.objects.create(event=event, team=first[0], score=first[1])
            EventStandings.objects.create(event=event, team=second[0], score=second[1])
            EventStandings.objects.create(event=event, team=third[0], score=third[1])

            # distribute rewards while accounting for ties
            if first[1] > second[1]:
                # single first
                players = EventPerformance.objects.filter(event=event, player__team=first[0])
                for playerPerf in players:
                    Player.objects.filter(id=playerPerf.player.id).update(
                        coins=F('coins') + (3 * playerPerf.contribution))

                if second[1] > third[1]:
                    # single second
                    players = EventPerformance.objects.filter(event=event, player__team=second[0])
                    for playerPerf in players:
                        Player.objects.filter(id=playerPerf.player.id).update(
                            coins=F('coins') + (2 * playerPerf.contribution))

                    players = EventPerformance.objects.filter(event=event, player__team=third[0])
                    for playerPerf in players:
                        Player.objects.filter(id=playerPerf.player.id).update(
                            coins=F('coins') + playerPerf.contribution)

                else:
                    # second third tie
                    players = EventPerformance.objects.filter(event=event, player__team__in=[second[0], third[0]])
                    for playerPerf in players:
                        Player.objects.filter(id=playerPerf.player.id).update(
                            coins=F('coins') + (2 * playerPerf.contribution))

            elif second[1] > third[1]:
                # first second tie
                players = EventPerformance.objects.filter(event=event, player__team__in=[first[0], second[0]])
                for playerPerf in players:
                    Player.objects.filter(id=playerPerf.player.id).update(
                        coins=F('coins') + (3 * playerPerf.contribution))

                players = EventPerformance.objects.filter(event=event, player__team=third[0])
                for playerPerf in players:
                    Player.objects.filter(id=playerPerf.player.id).update(
                        coins=F('coins') + playerPerf.contribution)

            else:
                # 3 way tie
                players = EventPerformance.objects.filter(event=event, player__team__in=[first[0], second[0], third[0]])
                for playerPerf in players:
                    Player.objects.filter(id=playerPerf.player.id).update(
                        coins=F('coins') + (3 * playerPerf.contribution))

            # clear area
            event.clear_area()

            # switch flag
            event.active = False
            event.save()

    # get the scores for events that finished after date that player participated in
    @staticmethod
    def event_scores(date, player):
        # get finished events
        today = datetime.date.today()
        # get only events that have ended and are not active and the player has participated in
        # get all events
        if date != '':
            events = Event.objects.filter(
                end__gte=date, end__lte=today, active=False,
                eventperformance__player=player).prefetch_related('eventperformance_set',
                                                                  'eventstandings_set').order_by('-end')
        # get only events that finished after date
        else:
            events = Event.objects.filter(
                end__lte=today, active=False,
                eventperformance__player=player).prefetch_related('eventperformance_set',
                                                                  'eventstandings_set').order_by('-end')

        ret = []
        for event in events:
            perfs = dict()

            # get user performance
            player_perf = event.eventperformance_set.first()
            perfs['user'] = player_perf.contribution

            # get team performance
            team_perfs = event.eventstandings_set.all()
            for team_perf in team_perfs:
                perfs[team_perf.team.name] = team_perf.score

            ret.append({'id': event.id, 'start': event.start, 'end': event.end, 'performance': perfs})

        return ret

    # check a point is within this event
    def check_within(self, point):
        """
        Input: list of events, point to test if inside an event polygon. Assumes no events overlap.
        Output: If point is in an event then that event otherwise None.

        """
        # calculate tile centre
        point = (point[0] + (UNIT_TILE_SIZE / 2), point[1] + (UNIT_TILE_SIZE / 2))
        point = Point(point)
        # define polygon using event bounds
        bounds = self.get_bounds()
        polygon = Polygon(bounds)
        # check if tile in within polygon bounds
        return polygon.contains(point)

    # get boundary points of this event
    def get_bounds(self):
        bounds = EventBounds.objects.filter(event_id=self.id).order_by('id')
        bounds_list = []
        for bound in bounds:
            bounds_list.append((bound.easting, bound.northing))
        return bounds_list

    # get all grids within this event
    def all_grids(self):
        """
        Input: Event object
        Output: List of all grids in the event.
        """
        bounds = self.get_bounds()

        # Subtract each bound by half of unit tile rounded (needs to be int to work) to get "center"
        # Translating the bounds to be in the "center" coordinate space instead of bottom left of each grid.
        for i in range(len(bounds)):
            bounds[i] = (bounds[i][0] - math.ceil(UNIT_TILE_SIZE / 2), bounds[i][1] - math.ceil(UNIT_TILE_SIZE / 2))

        xs, ys = zip(*bounds)

        # create a copy of the polygon translated to the origin.
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        newPoly = [(x - minx, y - miny) for (x, y) in bounds]

        # Create a grid to flood fill.
        # https://stackoverflow.com/questions/21339448/how-to-get-list-of-points-inside-a-polygon-in-python
        X = maxx - minx + 1
        Y = maxy - miny + 1
        grid = np.zeros((X, Y), dtype=np.int8)
        mahotas.polygon.fill_polygon(newPoly, grid)  # 1 if inside polygon 0 if not.

        # https://www.desmos.com/calculator/y3jwlc86vq
        # Retranslate the polygon back to original location and ensure that each grid is a unit tile size.
        grids = [(x + minx - 1, y + miny) for (x, y) in zip(*np.nonzero(grid)) if
                 ((x + minx - 1) % UNIT_TILE_SIZE == 0 and (y + miny) % UNIT_TILE_SIZE == 0)]
        return grids

    # delete all grids within the event
    def clear_area(self):
        """
        Input: event to clear grids in
        Output: None, deletes grids within event.
        """
        all_grids = self.all_grids()
        if all_grids is not None:
            Grid.objects.filter(reduce(operator.or_, (Q(easting=i, northing=j) for i, j in all_grids))).delete()

    # calculate the number of tiles each team owns within the event
    def winner(self):
        """
        Input: Event object
        Output: count the number of grids within event per team. ***Descending order***
        """

        all_grids = self.all_grids()
        if all_grids is not None:
            teams = Team.objects.filter(
                reduce(operator.or_, (Q(player__grid__easting=i, player__grid__northing=j) for i, j in all_grids)))
            return teams.values('name').annotate(total=Count('name')).order_by('-total')

    # get the centre of an event
    def center(self):
        """
        Input: Tuple of coordinates for polygon
        Output: Center of polygon coordinates
        """
        poly_bounds = Polygon(self.get_bounds())
        return poly_bounds.centroid.x, poly_bounds.centroid.y


# store information about event boundary points
class EventBounds(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    easting = models.PositiveIntegerField()
    northing = models.PositiveIntegerField()


# store information about how well each team did in a closed event
class EventStandings(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    score = models.PositiveIntegerField()


# store information about a user's workout
class Workout(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    duration = models.PositiveIntegerField()  # in seconds
    calories = models.PositiveIntegerField(default=0)
    type = models.CharField(max_length=10)  # e.g. walk, run
    points = models.PositiveIntegerField(default=0)  # number of grids touched in that workout
    date_recorded = models.DateTimeField(auto_now_add=True)


# store the points a user traveled through during a workout
class WorkoutPoint(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    time = models.DateTimeField()
    easting = models.PositiveIntegerField()
    northing = models.PositiveIntegerField()
    ghost = models.BooleanField(default=False)


# store the user's contribution to an event
class EventPerformance(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    contribution = models.PositiveIntegerField()


# store the details of an offensive map report
class ReportGrids(models.Model):
    easting = models.PositiveIntegerField()
    northing = models.PositiveIntegerField()
    time = models.DateTimeField()
    reported_by = models.ForeignKey(Player, on_delete=models.CASCADE)
    reason = models.CharField(max_length=100)
    area = models.PositiveIntegerField()
