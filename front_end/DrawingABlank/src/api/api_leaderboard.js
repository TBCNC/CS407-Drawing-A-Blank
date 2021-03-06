import { request, getToken } from "./api_networking.js";
//Obtain the points leaderboard from the back-end
export const getPointsLeaderboard = (date, teams) =>{
    var query = "/?date="+date;
    for(const team of teams){
        query+="&teams="+team;
    }
    return getToken().then(token => request('GET','leaderboard/points',query,'',token)).then(response => {
        if(response.status != 200){
            throw new Error('Could not obtain points leaderboard.');
        }
        return response.json();
    });
}
//Obtain the distance leaderboard from the back-end
export const getDistanceLeaderboard = (date, teams) =>{
    var query = "/?date="+date;
    for(const team of teams){
        query+="&teams="+team;
    }
    return getToken().then(token => request('GET','leaderboard/distance/',query,'',token)).then(response => {
        if(response.status != 200){
            throw new Error('Could not obtain distance leaderboard.');
        }
        return response.json();
    });
}