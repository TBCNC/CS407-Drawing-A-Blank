import { StyleSheet } from 'react-native';

export const styles = StyleSheet.create({
    leaderboard:{
        padding:15
    },
    leaderboard_title:{
        borderBottomColor:"#979797",
        borderBottomWidth:2,
        paddingBottom:5
    },
    leaderboard_title_text:{
        color:"black",
        fontSize:32,
        textAlign:'left'
    },
    leaderboard_entries:{
        paddingTop:15
    },
    leaderboard_entry:{
        borderBottomColor:"#979797",
        borderBottomWidth:2,
        flexDirection:'row',
        paddingBottom:5
    },
    leaderboard_entry_picture:{
        alignContent:'flex-start',
        padding:10
    },
    leaderboard_entry_picture_params:{
        width:64,
        height:64
    },
    leaderboard_entry_score:{
        justifyContent:'center',
        alignItems:'flex-end',
        marginLeft:'auto',
        paddingRight:10
    },
    leaderboard_entry_title:{
        alignContent:'space-around',
        justifyContent:'center'
    },
    leaderboard_entry_title_text:{
        fontSize:24,
        color:"black",
    },
    leaderboard_entry_score_text:{
        fontSize:24,
        color:"black",
        textAlign:'right'
    },
    summary:{
        padding:20,
    },
    summary_title:{
    },
    summary_title_text:{
        fontSize:32,
        color:"black",
        textAlign:"center"
    },
    summary_description_text:{
        fontSize:20,
        color:"black",
        textAlign:"center"
    },
    summary_status:{
    },
    summary_status_winner:{
        color:"#0fd945",
        fontSize:26,
        textAlign:"center"
    },
    summary_status_loser:{
        color:"#de1610",
        fontSize:26,
        textAlign:"center"
    },
    continue_button:{
        borderRadius:5,
        borderColor:"black",
        borderWidth:1,
        backgroundColor:"#6db0f6",
        width:"100%",
        alignSelf:"center"
    },

    continue_button_text:{
        textAlign:"center",
        fontSize:24
    },
});