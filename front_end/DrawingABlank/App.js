/**
 * For the moment, until we implement navigation, I'd say just let App.js just act as a place to test your UIs.
 */
import React, {useState} from 'react';
import Map from './src/components/mapView/Map.js';
import {StyleSheet, View} from 'react-native';

import {createStackNavigator} from '@react-navigation/stack';
import {NavigationContainer} from '@react-navigation/native';
import WorkoutPostStats from './src/components/workout_recording/workout_post_stats.js';
import MapViewCompleteComponent from './src/components/mapView/MapViewCompleteComponent.js';
import AccountAuthUI from './src/components/account_ui/account_ui.js';
import MapTutorial from './src/components/account_ui/tutorial_screens/MapTutorial.js';
import TutorialNavigation from './src/components/account_ui/tutorial_screens/TutorialNavigation.js';
import EventPodium from './src/components/events/EventPodium.js';
import EventSummary from './src/components/events/EventSummary.js';
import EventHistory from './src/components/events/EventHistory.js';
import LoadingScreen from './src/components/account_ui/loading_screen/loading_screen.js';
import WorkoutHistory from './src/components/workout_history/workout_history.js';
import Leaderboard from './src/components/leaderboard/leaderboard.js';
const Stack = createStackNavigator();

//Insert any code you wish to test here in order to see it. Note that before releasing the final version, we will want to change this back to the start screen.

export default function App() {
  console.log('Starting');
  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="account"
        screenOptions={{headerShown: false}}>
        <Stack.Screen name="account" component={AccountAuthUI} />
        <Stack.Screen
          name="map_view_complete"
          component={MapViewCompleteComponent}
        />
        <Stack.Screen name="post_workout_stats" component={WorkoutPostStats} />
        <Stack.Screen name="leaderboard" component={Leaderboard} />
        <Stack.Screen name="workout_history" component={WorkoutHistory} />
        <Stack.Screen name="event_history" component={EventHistory} />
        <Stack.Screen name="event_summary" component={EventSummary} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
