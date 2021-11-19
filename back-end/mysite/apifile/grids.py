import math
import bng
import numpy as np
from bresenham import bresenham
from pyproj import Transformer
from .models import Grid

"""
bng is main library used: https://pypi.org/project/bng/

Coordinate systems: Latitude longitude coordinates will use WGS84("EPSG:4326"): 
https://en.wikipedia.org/wiki/World_Geodetic_System British National grid(BNG) will use the 1936 datum OSGB36(
"EPSG:27700"): https://en.wikipedia.org/wiki/Ordnance_Survey_National_Grid 

Grid reference of BNG as = a String data type of form 2 letters followed by {4,6,8,10} integers.
latlong coordinates should be in a tuple: [0] = latitude, [1] = longitude

Note: conversions back and forth will introduce a slight error: can be by 1 square. 
Should be fine due to GPS error and latlong coordinate rounding. But can apparently fix by making a geoid correction.

Dealt with boundary conditions: e.g. SP 99999 99999 when incremented needs to modify the letter: Fixed by first 
converted to all numeric so that the library converts it to the correct letter.(cant just increment letter due to how 
the bng coordinates work) 

"""


def distance(point_a, point_b):
    a_east, a_north = bng.to_osgb36(point_a)
    b_east, b_north = bng.to_osgb36(point_b)
    return math.sqrt((a_east- b_east) ** 2 + (a_north - b_north) ** 2)


def calculate_speed(point_a, point_b, time_in_between):
    """
    Function input: 2 grid coordinates and the time taken to get from point A to point B
    Function output: the calculated speed in meters per unit time(for example if timeInbetween was in seconds then
    output is X m/s).
    """
    dist = distance(point_a, point_b)
    return dist / time_in_between

def calculate_radius(speed):

    #https://www.desmos.com/calculator/hhnpngcpsr
    return math.floor(-0.1000*speed*speed+1.500*speed)


def grid_to_latlong(grid):
    """
    Converts a BNG grid number to the latitude and longitude of the bottom left corner of the input grid.

    Function input: Grid reference of BNG as a string
    Function output: A tuple containing converted latitude and longitude (both floats).
    """

    # defines the transformation from UK ordinance survey to lat long
    transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326")

    # converts to numeric only grid references
    if type(grid) == str:
        x, y = bng.to_osgb36(grid)
    else:
        x, y = grid
    return transformer.transform(x, y)


def latlong_to_grid(latlong):
    """

    Function input: A tuple containing converted latitude and longitude (both floats): Requires a couple of decimal
    places for accuracy Function output: Grid reference of BNG as a string returns 2 letters + 10 digits.
    """
    # defines the transformation from lat long to UK ordinance survey
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:27700")

    # Converts to grid, specified 10 figs for accuracy.
    x, y = transformer.transform(latlong[0], latlong[1])
    return bng.from_osgb36((x, y), figs=10)


def bounds_of_grid(location, dist=1):
    """
    Returns the latitude and longitudes of the input grid. 
    The distance argument determines how large the grid is e.g. distance=1 means the grid is 1x1 meters.

    Function input: Grid reference as easting and northing tuple Function output: A list of tuples containing
    converted latitude and longitude coordinates for all 4 corners of the current grid.
    """

    if type(location) == str:
        easting, northing = bng.to_osgb36(location)
    else:
        easting, northing = location

    coordinates = []

    # grid references refer to the bottom left corner of the grid so need to get positively adjacent grids coordinates.
    grids = [(0, 0), (dist, 0), (dist, dist), (0, dist)]
    for i in range(len(grids)):
        new_eastings = easting + grids[i][0]
        new_northings = northing + grids[i][1]

        # convert to 2 letter + 10 digit form to convert to latlong
        new_grid = bng.from_osgb36((new_eastings, new_northings), figs=10)
        coordinates.append(grid_to_latlong(new_grid))

    return coordinates


def points_in_circle_np(radius, x0=0, y0=0):
    """
    https://stackoverflow.com/questions/49551440/python-all-points-on-circle-given-radius-and-center
    """
    x_ = np.arange(x0 - radius - 1, x0 + radius + 1, dtype=int)
    y_ = np.arange(y0 - radius - 1, y0 + radius + 1, dtype=int)
    x, y = np.where((x_[:, np.newaxis] - x0) ** 2 + (y_ - y0) ** 2 <= radius ** 2)
    # x, y = np.where((np.hypot((x_-x0)[:,np.newaxis], y_-y0)<= radius)) # alternative implementation
    for x, y in zip(x_[x], y_[y]):
        yield x, y


def grids_in_radius(position, radius=4):
    """
    Function input: Current latitude longitude position
    Function output: A list of grids within the radius.
    """
    x, y = position
    # seems fine for now, could set the function's center at 0,0 and just
    # add the offset to the origin of the square.
    grids = points_in_circle_np(radius, x, y)  

    #grids = list(map(lambda p: bng.from_osgb36(p, figs=10), grids))
    return grids


def grids_in_path(point_a, point_b):
    """
    Function input: Current and old easting and northing tuples
    Function output: A list of grids within the straight line path.

    Library: https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm
    """

    east_a, north_a = point_a
    east_b, north_b = point_b

    # Using the bresenham line algorithm implemented using a library.
    grids = list(bresenham(east_a, north_a, east_b, north_b))

    # https://stackoverflow.com/questions/10212445/map-list-item-to-function-with-arguments
    #grids = list(map(lambda p: bng.from_osgb36(p, figs=10), grids))

    return grids

def all_grids_with_path(point_a, point_b, radius):
    """
    All grids in the path given the old and current easting and northings including the radius around the path to colour in.
    """
    point_a = bng.to_osgb36(point_a)
    point_b = bng.to_osgb36(point_b)
    grids_path = grids_in_path(point_a, point_b)
    
    #lots of overlapping circles so use set to remove duplicates (seems fine for efficiency for now).
    all_grids = set()   
    for grid in grids_path:
        grids_radius = grids_in_radius(grid,radius)
        all_grids.update(grids_radius)

    return all_grids

def super_sample(tiles, zoom_level=1):
    """
    uses all tiles visible and ensures that not too many grids are sent back to the user.
    
    """

    allCoords = []

    #group grids into NxN blocks based on zoom level: where zoom_level=1 means no division and zoom_level=1 means 2x2 blocks.

    #get the average colour per nxn block

    #get coordinates of the entire nxn block

    #return this data to user
    return allCoords





def grids_visible(coords):
    """
    Function input: 4 longitude/latitude coordinates that the screen can see
    Function output: coordinates of every grid that is visible.
    """
    # if quadrilateral and bottomleft < topRight then only need two coords.
    bottomLeft = coords[0]
    topRight = coords[2]

    blGrid = latlong_to_grid(bottomLeft)
    trGrid = latlong_to_grid(topRight)

    lower_east, lower_north = bng.to_osgb36(blGrid)
    upper_east, upper_north = bng.to_osgb36(trGrid)

    allCoords = []

    # this is quite slow: zooming out means theres a lot of grids and repeated coordinates/calculations Could fix by
    # "super sampling" grids e.g. 4 1x1m grids average their colour to make 1 4x4m grid. (only need to access colour)
    # or by saving coordinates to not calculate again. Then you can access less coordinates and do less calculations.
    tiles = Grid.objects.filter(northing__range=(lower_north, upper_north),
                                easting__range=(lower_east, upper_east))

    for tile in tiles:
        allCoords.append({"colour": tile.team.colour, "bounds": bounds_of_grid((tile.easting, tile.northing))})

    return allCoords


def grids_visible_alt(coords):
    """
    Function input: 4 longitude/latitude coordinates that the screen can see
    Function output: coordinates of every grid that is visible.
    """
    # if quadrilateral and bottomleft < topRight then only need two coords.
    bottomLeft = coords[0]
    topRight = coords[2]

    blGrid = latlong_to_grid(bottomLeft)
    trGrid = latlong_to_grid(topRight)

    lower = bng.to_osgb36(blGrid)
    upper = bng.to_osgb36(trGrid)
    lower_east = round(lower[0])
    lower_north = round(lower[1])
    upper_east = round(upper[0])
    upper_north = round(upper[1])

    bounds = np.zeros(shape=(upper_east - lower_east + 2, upper_north - lower_north + 2, 2))
    colours = np.zeros(shape=(upper_east - lower_east + 1, upper_north - lower_north + 1), dtype="S6")

    # this is quite slow: zooming out means theres a lot of grids and repeated coordinates/calculations Could fix by
    # "super sampling" grids e.g. 4 1x1m grids average their colour to make 1 4x4m grid. (only need to access colour)
    # or by saving coordinates to not calculate again. Then you can access less coordinates and do less calculations.
    tiles = Grid.objects.filter(northing__range=(lower_north, upper_north),
                                easting__range=(lower_east, upper_east))
    for tile in tiles:
        index = (tile.easting - lower_east, tile.northing - lower_north)
        colours[index[0]][index[1]] = tile.team.colour
        for bound in ((0, 0), (1, 0), (0, 1), (1, 1)):
            if bounds[index[0] + bound[0]][index[1] + bound[1]][0] == 0:
                coords = grid_to_latlong((tile.easting + bound[0], tile.northing + bound[1]))
                bounds[index[0] + bound[0]][index[1] + bound[1]][0] = coords[0]
                bounds[index[0] + bound[0]][index[1] + bound[1]][1] = coords[1]

    return {"colour": colours.tolist(), "bounds": bounds.tolist()}
