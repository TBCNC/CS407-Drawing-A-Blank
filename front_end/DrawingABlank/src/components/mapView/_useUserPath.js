import React, {useEffect, useRef, useState} from 'react';

import {Workout} from '../workout_recording/workout';
import useGeoLocation from './useGeoLocation';
import {Polyline} from 'react-native-maps';

const recorder = new Workout(); // maybe should be a ref, idk
const USER_INK_COLOUR = 'rgba(0, 255, 0, 0.75)';

// normal path tracing vs workout path tracing
export default function useUserPath() {
  const workout_active = useRef(false);
  const userLocation = useGeoLocation();
  const [userPath, setUserPath] = useState([]);

  // might have to be careful about init userlocation being tracked i.e. (0,0)
  // useEffect(() => {
  //   if (workout_active.current) addPathPoint(userLocation.current);
  // }, [userLocation.current]);

  function removePathPoint(id) {
    userPath.current = userPath.current.pop();
  }

  function addPathPoint(latLngPoint, isTracking) {
    // add latlng point to path
    //console.log('adding points', userPath, latLngPoint);
    if (workout_active.current) setUserPath([...userPath, latLngPoint]);
    //setUserPath([...userPath, latLngPoint]);
    //console.log('Added Points', userPath);
    // add point to workout recorder / exercise computer
    recorder.addCoordinate(
      latLngPoint.latitude,
      latLngPoint.longitude,
      isTracking,
    );
  }

  function clearPath() {
    setUserPath([]);
  }

  function toggleWorkoutActive() {
    if (workout_active.current) stopWorkout();
    else startWorkout();
  }

  function startWorkout() {
    console.log('Starting Workout...');
    const {latitude, longitude} = userLocation.current;

    clearPath();
    recorder.startWorkout();
    recorder.addCoordinate(latitude, longitude, true);
    workout_active.current = true;
  }

  function stopWorkout() {
    console.log('Stopping Workout...');

    recorder.stopWorkout();
    workout_active.current = false;
    clearPath();
  }

  function DrawUserPath() {
    if (workout_active) {
      // console.log('drawing path,', userPath);
      return (
        <Polyline
          coordinates={userPath}
          strokeWidth={3 || USER_DRAW_DIAMETER}
          strokeColor={USER_INK_COLOUR}
        />
      );
    } else {
      return false;
    }
  }

  return [
    DrawUserPath,
    startWorkout,
    stopWorkout,
    addPathPoint,
    workout_active,
  ];
}
