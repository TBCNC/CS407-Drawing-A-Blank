import {request} from './api_networking.js';
import * as geolib from 'geolib';

/**
 * 
 * @param {JSON Object} bounds | The bounds of the event which will be used to calculate a centre 
  @returns {Latitude and Longitude} marker | The position of the marker
*/
function getMarkerPosition(bounds){
  //This is assuming for the moment that everything is in the correct ordering, which is a non-self-intersecting polygon of n vertices
  //This code has been adapted from the following Wikipedia formula: https://en.wikipedia.org/wiki/Centroid#Of_a_polygon
  //Also assuming that latitude is "x" and longitude is "y", and the error obtained by doing this is negligible.
  //It is important to note the last part, which states that the last case must loop.
  //First, compute the area
  var area = 0.0;
  for(var i = 0; i < bounds.length; i++){
    area += (bounds[i][0]*bounds[(i+1)%bounds.length][1] - bounds[(i+1)%bounds.length][0]*bounds[i][1])/2;
  }

  //Compute the centre x and centre y
  var centre_x = 0.0;
  var centre_y = 0.0;
  for(var i = 0; i < bounds.length; i++){
    centre_x += ((bounds[i][0] + bounds[(i+1)%bounds.length][0]) * (bounds[i][0]*bounds[(i+1)%bounds.length][1] - bounds[(i+1)%bounds.length][0]*bounds[i][1]))/(6*area);
    centre_y += ((bounds[i][1] + bounds[(i+1)%bounds.length][1]) * (bounds[i][0]*bounds[(i+1)%bounds.length][1] - bounds[(i+1)%bounds.length][0]*bounds[i][1]))/(6*area);
  }

  return {"latitude":centre_x, "longitude":centre_y};
}

function getBoundsAsJSON(bounds){
  var result = [];
  for(var i = 0; i < bounds.length; i++){
    result.push({"latitude":bounds[i][0], "longitude":bounds[i][1]});
  }
  return result;
}

function convertToGeoLib(coordinate){
  return {"latitude":coordinate[0],"longitude":coordinate[1]};
}

/*
  This is assuming that grids obtained and passed here cover the entire event area. This is also assuming that the grid size given
  accurately reflects the status of the event. (i.e. lowest possible grid size).
*/
export const getEventScores = (grids, event_bounds) => {
  var event_conversion = [];
  for(var i = 0; i < event_bounds.length; i++){
    event_conversion.push(convertToGeoLib(event_bounds[i]));
  }
  var filtered_grids = grids.filter((grid) => {
    var converted_bounds = [];
    for(var i = 0; i < grid.bounds.length; i++){
      converted_bounds.push(convertToGeoLib(grid.bounds[i]));
    }
    var center_point = geolib.getCenterOfBounds(converted_bounds);
    geolib.isPointInPolygon(center_point, event_bounds);
  });
  //https://stackoverflow.com/questions/56375737/get-count-of-array-objects-belonging-to-a-partical-id-in-javascript-node-js
  var colour_counts = {};
  filtered_grids.forEach((grid) => {
    if(!colour_counts[grid.colour])
      colour_counts[grid.colour] = 0;
    colour_counts[grid.colour]++;
  });
  var results = [];
  Object.keys(colour_counts).forEach((colour) => {
    results.push({"colour":colour, "count":colour_counts[colour]});
  });
  return results.sort((a,b) => a.count - b.count);
}

export const getEvents = () => {
  return request('GET', 'current-events', '', '')
    .then(response => response.json())
    .then(data => {
      console.log("Got:"+JSON.stringify(data));
      var result = [];
      for (var key in data) {
        var curr_object = data[key];

        var new_object = {
          //No title or description has been provided by the endpoint at the moment.
          //Therefore, we are going to use default title names.
          id: key,
          title: 'Title for Event ' + key,
          description: 'Description for Event ' + key,
          bounds: {
            coordinates:getBoundsAsJSON(curr_object.bounds),
            //Change these details if added by back-end
            strokeColor:"#000",
            fillColor:"rgba(43, 145, 222, 0.2)",
            strokeWidth:1,
            name: 'Area for event ' + key,
            id: key,
          },
          marker: getMarkerPosition(curr_object.bounds),
          date_start: curr_object.start,
          date_end: curr_object.end
        };
        result.push(new_object);
      }
      console.log('Returning :' + JSON.stringify(result));
      return result;
    })
    .catch(err => console.log(err));
}
