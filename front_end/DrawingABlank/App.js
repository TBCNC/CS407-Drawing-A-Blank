/**
 * For the moment, until we implement navigation, I'd say just let App.js just act as a place to test your UIs.
 */
<<<<<<< HEAD
import { StatusBar } from 'expo-status-bar';
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import WorkoutScreen from './src/components/workout_recording/workout_screen';

export default function App() {
  return(
    <WorkoutScreen/>
=======
import React, {useState} from 'react';
import Map from './src/components/mapView/Map.js';
import {StyleSheet, View} from 'react-native';

import OverlayDemo from './src/containers/OverlayDemo';
import {styles} from './src/components/mapView/style';
import EventDetails from './src/components/events/EventDetails';
import ExampleOverlay from './src/components/events/ExampleOverlay';
import Overlay from './src/containers/Overlay';

export default function App() {
  const [overlayVisible, setOverlayVisible] = useState(false);
  // use setOverlayContent to change the content of the overlay
  const [overlayContent, setOverlayContent] = useState();

  return (
    <View style={styles.mapContainer}>
      <Map
        setOverlayVisible={setOverlayVisible}
        setOverlayContent={setOverlayContent}
      />
      <Overlay
        visible={overlayVisible}
        setVisible={setOverlayVisible}
        children={overlayContent}
      />
    </View>
>>>>>>> frontend_api_events
  );
}