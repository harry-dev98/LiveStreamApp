"use strict"

const configuration = {
    'iceServers' : [{
        "urls" : "stun:stun.l.google.com:19302"
    }]
};
var offerConstraints = {
    offerToReceiveAudio : 1,
    offerToReceiveVideo : 1
};
let Users = [];
let user;
let localStream;
let remoteDesc; 
let mediaRecorder;
let recordedBlobs;

var video = document.getElementById('video');
let dropArea = document.getElementById('drop-area');
let button = document.getElementById("button");
let msgBox = document.getElementById("msgContainer")
let fileCount = 0;
let files;

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, (e)=>{
        e.preventDefault();
        e.stopPropagation();
    }, false);
});
['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, (e)=>{
        dropArea.classList.add('highlight');
    }, false);
});
['dropleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, (e)=>{
        dropArea.classList.remove('highlight');
        }, false);
});

function addImg(file){
    let div = document.createElement("div");
    div.className = "col-md-7 col-xs-7 col-sm-7 col-lg-7 doc";
    let img = document.createElement('img');
    img.src = file;
    img.alt="Failed To Load Image";
    img.setAttribute('height', '875px');
    img.setAttribute('width', '1100px');
    // img.height = "100%";
    // img.width = "100%";
    div.appendChild(img);
    msgBox.appendChild(div);
}

function addpdf(file){
    let div = document.createElement("div");
    div.className = "col-md-7 col-xs-7 col-sm-7 col-lg-7 doc";
    var ifrm = document.createElement('iframe');
    ifrm.setAttribute('id', 'ifrm');
    ifrm.setAttribute('height', '875px');
    ifrm.setAttribute('width', '1100px'); // assign an id
    ifrm.src = file;
    div.appendChild(ifrm);
    msgBox.appendChild(div);
}

dropArea.addEventListener('drop',(e)=>{
    let dt = e.dataTransfer;
    files = Array.from(dt.files);
    if(files.length>1){
        console.log("onefile at a time..");
        return;
    }
    fileCount = fileCount + files.length;
    dropArea.style.display="none";
    setTimeout(async()=>{dropArea.style.display='block';}, 3000);
    files.forEach(async (file)=>{   
        let promise = new Promise((resolve, reject)=>{
            if(file) setTimeout(resolve(file), 1000);
            else reject("no file to send");
        })
        await promise
        .then(preview_send(file))
        .catch((err)=>{
            console.log(err);
        });
    });
}, false);


async function send_metaData(DataChann, file){
    console.log("metadata sending of "+file.name);
    let name = file.name;
    let size = file.size;
    let type = file.type;
    let send_d = JSON.stringify({
        "file" : name,
        "size" : size,
        "type" : type
    });
    await DataChann.send(send_d);
    await webCamSocket.send(send_d);
    console.log("metadata sent of "+file.name);
    return DataChann;
}

async function send_chunks(DataChann, file){
    console.log("sending chunks of "+file.name);
    let chunk = 8 * 1024 * 1024;
    let left = file.size;
    let offset=0;
    while(left>0){
        chunk = (chunk > left) ? left : chunk;
        var slice = file.slice(offset, offset+chunk);
        await webCamSocket.send(slice);
        await DataChann.send(slice);
        left -= chunk;
        offset += chunk;
        console.log("sent ",(file.size-left),"/",file.size);
    }
    console.log("sent file.. "+ file.name);   
}

async function preview_send(file){
    console.log("file..",file);
    var objectURL = URL.createObjectURL(file);
    var Ext = file.name.substring(file.name.lastIndexOf('.') + 1).toLowerCase();
    console.log("extension of file is "+ Ext);
    if (Ext=="gif"||Ext=="png"||Ext=="bmp"||Ext=="jpeg"||Ext=="jpg"){
        addImg(objectURL);
    }
    else if(Ext == "pdf"){
        addpdf(objectURL);
    }
    for (const [user, U] of Object.entries(Users)){
    console.log("user..", user);
    let DataChann = U.datachann;
    await send_metaData(DataChann, file)
    .then(send_chunks(DataChann, file))
    .catch((err)=>{
        console.log("error while sending ", err);
        })
    };
}


if(navigator.mediaDevices){
    console.log("need permissions to user media devices");
    navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: {exact: true}
        },
        video: {
          width: 1280, height: 720
        }
      })
    .then(stream=>{
        console.log("media devices acquired..");
        localStream = stream;
        video.srcObject = stream;
        video.play();
        return stream;
    })
    .then(()=>{
        console.log("started recording..")
        startRecording();
    })
    .catch(err=>{
        console.log("error while accesing media", err);
    })
}

function startRecording() {
    recordedBlobs = [];
    let options = {
        mimeType : 'video/webm;codecs=vp9'
    };
    if(!MediaRecorder.isTypeSupported(options.mimeType)){
        console.log(options.mimeType, " is not supported!!");
        options = {
            mimeType : 'video/webm;codecs=vp8'
        };
        if(!MediaRecorder.isTypeSupported(options.mimeType)){
            console.log(options.mimeType, " is not supported!!");
            options = {
                mimeType : 'video/webm'
            };
            if(!MediaRecorder.isTypeSupported(options.mimeType)){
                console.log(options.mimeType, " is not supported!!");
                options = {
                    mimeType : ''
                };
            }
        }    
    }
    try{
        mediaRecorder = new MediaRecorder(localStream, options);
    }
    catch(err){
        console.log("Not recording.. ", err);
    }
    mediaRecorder.ondataavailable = (event)=>{
        if(event.data && event.data.size>0){
            recordedBlobs.push(event.data);
        }
    }
    mediaRecorder.start(10);
}

function download(){
    mediaRecorder.stop();
    const blob = new Blob(recordedBlobs, {type:'video/webm'});
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = 'recording.webm';
    a.click();
    setTimeout(()=>{
        document.body.removeChild('a');
        window.URL.revokeObjectURL(url);
    }, 10000);
}

let offer = async (Conn, user)=>{
    console.log("creating an offer for ", user);
    await Conn.createOffer(offerConstraints)
    .then(async (offer)=>{
        console.log("setting local Description..");
        await Conn.setLocalDescription(offer);
        return Conn.localDescription;
    })
    .then(async (desc)=>{
        console.log("sending offer...");
        await webCamSocket.send(JSON.stringify({
            "offer" : desc,
            "for" : user
        }))
    })
    .catch((err)=>{
        console.log("there was trouble sending offer...", err);
        setTimeout(offer, 1000);
    })
};

webCamSocket.onmessage = (event)=>{
    console.log("websocket recieved a message..");
    let data = JSON.parse(event.data);
    if(data.recv == "answer"){
        console.log("recieved a answer..");
        let ansDesc = data["answer"];
        user = data["by"]
        let Conn = Users[user]["conn"];
        (new Promise(async (resolve, reject)=>{
            console.log("getting a session object from answer");
            try{
                resolve(new RTCSessionDescription(ansDesc));
            }
            catch(err){
                reject(err);
            } 
        })
        .then(async (ans)=>{
            console.log("setting remote Desc..");
            await Conn.setRemoteDescription(ans);
        })
        .catch((err)=>{
            console.log("encountered error while setting remote Desc")
        }));
    }
    else if(data.recv == "iceCand"){
        user = data.by;
        try{
            console.log("adding candidates..");
            Users[user]["conn"].addIceCandidate(data["candidate"]);
        }
        catch(e){
            console.log("error occured while adding candidates.. ", e);
        }
    }
    
    else if(data.recv == "open"){
        console.log(data.open)
    }
    
    else if(data.recv == "close"){
        console.log(data.close);
        delete Users[data.user];
    }

    else if(data.recv == "open_broadcast"){
        console.log(data.open_broadcast); 
        user = data.user;
        Users[user] = {
            "userId" : data.userId,
            "conn" : new RTCPeerConnection(configuration)
        };
        Users[user]["datachann"] = Users[user]["conn"].createDataChannel(user+"_datachann");
        console.log("created instance of a new user.. conn aswell as data channel")
        new Promise((resolve, reject)=>{
            try{
                resolve(Users[data.user]);
            }
            catch(err){
                reject(err);
            }
        })
        .then((U)=>{
            let Conn = U.conn;
            let Chann = U.datachann;
            Conn.onicecandidate = async (event)=>{
                console.log("handling the connections.. of ", user);
                const iceCand = event.candidate;
                if(iceCand){
                    await webCamSocket.send(JSON.stringify({
                        "who" : "host",
                        "for" : user,
                        "candidate" : iceCand
                    }));
                }
            };
            Conn.oniceconnectionstatechange = (event)=>{
                console.log("handling the connection change... of ", U.user);
                // console.log(event);
            };
            Conn.onerror = (event)=>{
                console.log(U.user+" Conn encountered an error "+event);
            };
            Chann.onopen = (event)=>{   
                console.log(U.user+" Channel's ready state is "+ Chann.readyState);
            };
            Chann.onclose = (event)=>{
                console.log(U.user, " Channel's ready state is ", Chann.readyState);
            };
            Chann.onerror = (event)=>{
                console.log("Error in DataChannel for "+ U.user+" "+event);
            }
            localStream.getTracks().forEach(track => Conn.addTrack(track, localStream));
            offer(Conn, user);
        });
    }
}


