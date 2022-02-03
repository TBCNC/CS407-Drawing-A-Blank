import { RecyclerViewBackedScrollViewBase } from "react-native";
import { request, setToken } from "./api_networking.js";

export const createUser = (username, email, password, team) => {
    body = {
        "username":username,
        "email":email,
        "password":password,
        "team":team
    };
    console.log("Sending create user request with " + JSON.stringify(body));
    return request('POST','user/','',JSON.stringify(body))
    .then(response=>{
        if(response.status != 200){
            throw new Error(JSON.stringify(response.json()));
        }
        return response.json()
    }).then(res=>{console.log("GOT TOKEN RESPONSE:"+res);setToken(res.token)});
}

export const authenticateUser = (username,password) => {
    body = {
        "username":username,
        "password":password
    };
    console.log('Sending authentication request with ' + JSON.stringify(body));
    return request('POST','api-token-auth/','',JSON.stringify(body))
    .then(response=>{
        if(response.status != 200){
            console.log(response);
            console.log(response.status);
            throw new Error('Incorrect credentials.');
        }
        return response.json();
    }).then(res => setToken(res.token));
}