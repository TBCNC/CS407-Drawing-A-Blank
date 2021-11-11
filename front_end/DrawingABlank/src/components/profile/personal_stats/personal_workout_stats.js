import React, {Component} from 'react';
import {Text, View} from 'react-native';
import WorkoutLineGraph from './graph/line_graph.js';
import ExtraData from './extra_data.js';
import { styles } from './style.js';

class PersonalWorkoutStats extends Component{
    render(){
        const data = [ 50, 10, 40, 95, -4, -24, 85, 91, 35, 53, -53, 24, 50, -20, -80 ]
        return(
            <View style={styles.main}>
                <WorkoutLineGraph graphTitle="Speed vs. Time"
                                    yData={data}>

                </WorkoutLineGraph>
                <ExtraData></ExtraData>
            </View>
        )
    }
}
export default PersonalWorkoutStats;