"use strict"

var offerConstraints = {
    offerToReceiveVideo : 1,
    offerToReceiveAudio : 1
};

var userId;
var User;
var isPeer = true;
var remoteStream;

var video = document.getElementById('video');
var msgBox = document.getElementById('msgContainer');

const configuration = {
    'iceServers' : [{
        "urls" : "stun:stun.l.google.com:19302"
    }]
};

let localPeerConn = new RTCPeerConnection(configuration);
console.log("RTCPeerConn established..");
localPeerConn.onicecandidate = (event)=>{
    console.log("handling the connections");
    const iceCand = event.candidate;
    if(iceCand){
        webCamSocket.send(JSON.stringify({
            "who" : "peer",
            "by" : User,
            "candidate" : iceCand
        }));
    }
}

localPeerConn.oniceconnectionstatechange = (event)=>{
    console.log("handling the connection change...");
    // console.log(event);
}

localPeerConn.ontrack = (event)=>{
    console.log("recieved mediaa.. from host");
    video.srcObject = event.streams[0];
    // video.play();
};

function addImg(objURL){
    let div = document.createElement("div");
    div.className = "col-md-7 col-xs-7 col-sm-7 col-lg-7 doc docExpand";
    let img = document.createElement('img');
    img.src = objURL;
    img.alt="Failed To Load Image";
    // img.setAttribute('height', '875px');
    // img.setAttribute('width', '1100px');
    img.setAttribute('class', 'docExpand');
    div.appendChild(img);
    msgBox.appendChild(div);
}

function addpdf(objURL){
    let div = document.createElement("div");
    div.className = "col-md-7 col-xs-7 col-sm-7 col-lg-7 doc docExpand";
    var ifrm = document.createElement('iframe');
    ifrm.setAttribute('id', 'ifrm'); // assign an id
    ifrm.src = objURL;
    ifrm.setAttribute('class', 'docExpand');
    // ifrm.setAttribute('height', '875px');
    // ifrm.setAttribute('width', '1100px');
    div.appendChild(ifrm);
    msgBox.appendChild(div);
}

let fname;
let size;
let type;
let chunk = 8 * 1024 * 1024;
let recieved=0;
let recievedBlob;
let DataChannel = localPeerConn.createDataChannel(User+"_datachann");
localPeerConn.ondatachannel = (event)=>{
    var recvChann = event.channel;
    console.log("ondatachannel..", event);
    recvChann.onmessage = (event)=>{
        console.log("recieved...", event);
        if(event.data instanceof Blob){
            let data = event.data;
            recieved += data.size;
            recievedBlob = new Blob([recievedBlob, event.data], {'type': recievedBlob.type});
            if(recieved == size){
                console.log("recieved complete file.. ", recievedBlob);
                var objectURL = URL.createObjectURL(recievedBlob);
                var Ext = fname.substring(fname.lastIndexOf('.') + 1).toLowerCase();
                console.log("extension of file is "+ Ext);
                if (Ext=="gif"||Ext=="png"||Ext=="bmp"||Ext=="jpeg"||Ext=="jpg"){
                    addImg(objectURL);
                }
                else if(Ext == "pdf"){
                    addpdf(objectURL);
                }
                recievedBlob = new Blob();
                recieved = 0;
            }
        }
        else{
            let data = JSON.parse(event.data);
            fname = data.file;
            size = data.size;
            type = data.type;
            recievedBlob = new Blob([], {'type':type});
        }
    }
};

webCamSocket.onmessage = async (event)=>{
    let data = JSON.parse(event.data);
    console.log("websocket recieved a message.. ", data.recv);
    if(data.recv == "offer"){
        console.log("recieved a offer..");
        let offerDesc = data["offer"];
        new Promise(async (resolve, reject)=>{
            console.log("getting a session object of offer");
            try{
                resolve(new RTCSessionDescription(offerDesc));
            }
            catch(err){
                reject(err);
            }
        }).then(async (offer)=>{
            console.log("setting remote Desc")
            await localPeerConn.setRemoteDescription(offer);
        })
        .catch((err)=>{
            console.log("got an error setting remote Desc..", err);
        })
        .finally(async ()=>{
            console.log("remote Desc has been set..")
            console.log("creating an answer to the offer");
            await localPeerConn.createAnswer()
            .then(async (answer)=>{
                console.log("localDesc has been set");
                await localPeerConn.setLocalDescription(answer);
                return localPeerConn.localDescription;
            })
            .then(async (desc)=>{
                console.log("sending answer..")
                await webCamSocket.send(JSON.stringify({
                    "answer": desc,
                    "by" : User
                }));
            })

        })
    }
    else if(data.recv == "iceCand"){
        try{
            console.log("adding candidates..");
            localPeerConn.addIceCandidate(data["candidate"]);
        }
        catch(err){
            console.log("error occured while adding candidates.. ", err);
        }
    }
    else if(data.recv == "open"){
        userId = data.userid;
        User = data.user;
        console.log(User, "User is instantiated as ", userId);
    }

}