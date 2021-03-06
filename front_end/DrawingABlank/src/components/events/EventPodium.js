import React, {Component} from 'react';
import {View} from 'react-native';
import {styles} from './style.js';
import { BarChart, XAxis } from 'react-native-svg-charts';
import { Text as SVGText } from 'react-native-svg';
import { Image as SVGImage } from 'react-native-svg';
import * as scale from 'd3-scale';

class EventPodium extends Component{
    //COLOURS:
    //OCEAN: 47C4FF
    //TERRA: FF8C91
    //WINDY: 82FF8A
    /*
        IN ORDER OF FIRST,SECOND,LAST
        [teamName : String]
    */
   //"My hope is this code is so awful that I am never allowed to write UI code again.."
    normalizeScore = (points, lowest_points, highest_points) =>{
        return 3*(points-lowest_points)/(highest_points-lowest_points)
    }
    render() {
        //Based of the following example: https://github.com/JesperLekland/react-native-svg-charts-examples/blob/master/storybook/stories/bar-chart/vertical-with-labels.js
        const TEAM_COLOURS = {"terra":"#FF8C91","windy":"#82FF8A","ocean":"#47C4FF"}
        const TEAM_AVATARS = {"terra":require('../../assets/img/terra.png'),"windy":require('../../assets/img/windy.png'),"ocean":require('../../assets/img/ocean.png')}
        const PODIUM_DATA = [
            {
                value: this.normalizeScore(this.props.points[2],this.props.points[2],this.props.points[0]),
                svg: {
                    fill: TEAM_COLOURS[this.props.teams[2]],
                },
                picture: TEAM_AVATARS[this.props.teams[2]],
                points:this.props.points[2]
            },
            {
                value: this.normalizeScore(this.props.points[0],this.props.points[2],this.props.points[0]),
                svg: {
                    fill: TEAM_COLOURS[this.props.teams[0]],
                },
                picture: TEAM_AVATARS[this.props.teams[0]],
                points:this.props.points[0]
            },
            {
                value: this.normalizeScore(this.props.points[1],this.props.points[2],this.props.points[0]),
                svg: {
                    fill: TEAM_COLOURS[this.props.teams[1]],
                },
                picture: TEAM_AVATARS[this.props.teams[1]],
                points: this.props.points[1]
            },
        ]
        const PODIUM_IMAGE_POS = 70
        const Labels = ({ x, y, bandwidth, data }) => (
                data.map((value, index) => (
                    <SVGImage
                        key={ index }
                        x={ x(index) + (bandwidth / 4) }
                        y={ y(value["value"]) - PODIUM_IMAGE_POS }
                        fontSize={ 14 }
                        width={64}
                        height={64}
                        fill={ 'black' }
                        alignmentBaseline={ 'middle' }
                        textAnchor={ 'middle' }
                        href={value.picture}
                    >
                    </SVGImage>
                ))
        )


        return (
            <View style={{height: this.props.height}}>
                <BarChart
                    style={{ height:"100%", flex:1 }}
                    data={PODIUM_DATA}
                    svg={{ fill: 'rgba(134, 65, 244, 0.8)' }}
                    contentInset={{ top: 10, bottom: 10 }}
                    spacing={0.2}
                    gridMin={0}
                    gridMax={5}
                    yAccessor={({ item }) => item.value}
                >
                    <Labels/>
                </BarChart>
                
                <XAxis
                    style={{ marginTop: 0 }}
                    data={ PODIUM_DATA }
                    scale={scale.scaleBand}
                    formatLabel={ (value, index) => PODIUM_DATA[index].points + " points" }
                    labelStyle={ { color: 'black' } }
                />
            </View>
        )
    }

}

export default EventPodium;