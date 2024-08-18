const refGambleButton = document.querySelector("#dropBallButton");
const refPlinkoGame = document.querySelector("#plinkoGame");
const refPlinkoWrapper = document.querySelector("#plinkoWrapper");
const refLamCoinText = document.querySelector("#lamCoinText");
const refBGM = document.querySelector("#bgmAudio");
const bucketInfo = [[10, "#ff0000"],
                [8, "#ff3200"],
                [6, "#ff5000"],
                [3.5, "#ff6400"],
                [2, "#ff7d00"],
                [1.2, "#ff9b00"],
                [1, "#ffb900"],
                [0.7, "#ffcd00"],
                [0.5, "#fff000"],
                [0.7, "#ffcd00"],
                [1, "#ffb900"],
                [1.2, "#ff9b00"],
                [2, "#ff7d00"],
                [3.5, "#ff6400"],
                [6, "#ff5000"],
                [8, "#ff3200"],
                [10, "#ff0000"]
            ];
var Engine = Matter.Engine,
    Render = Matter.Render,
    Runner = Matter.Runner,
    Bodies = Matter.Bodies,
    Events = Matter.Events,
    World = Matter.World,
    Composite = Matter.Composite;
var plinkoBalls = [];
var buckets = [];
var pegs = [];
var engine = Engine.create();
var render = Render.create({
    canvas: refPlinkoGame,
    engine: engine,
    options: {wireframes: false,
            height: 700,
            width: 850,}
});
refBGM.volume = 0.1;
var playOnInteract = document.addEventListener("click", function() {
    refBGM.play();
    document.removeEventListener(playOnInteract);
});

for (let i = 0; i < bucketInfo.length; i++) {
    var newBucket = Bodies.rectangle(22.5 + (45 * (i+1)), 650, 40, 30, {label: "bucket", isStatic: true, value: bucketInfo[i][0], chamfer: {radius: [5,5,5,5]}, render: {fillStyle: bucketInfo[i][1]}});
    var newText = document.createElement("p");
    newText.classList.add("bucketMultiplierText");
    newText.innerHTML = bucketInfo[i][0] + "x";
    newText.style.left = 45 * (i+1) + "px";
    refPlinkoWrapper.appendChild(newText);
    buckets.push(newBucket);
}
Composite.add(engine.world, buckets);

for (let i = 0; i < 16; i++) {
    let startingXoffset = 425 - (i+2) * 22.5;
    for (let j = 0; j < i + 3; j++) {
        var newPeg = Bodies.circle(startingXoffset + j * 45, 50 + i*37.5, 5, {label: "peg", isStatic: true, render: {fillStyle: "white"}})
        pegs.push(newPeg);
    }
}
Composite.add(engine.world, pegs);

refGambleButton.addEventListener("click", function() {
    const ballValue = parseFloat(refBallValueField.value);
    var renderProperties = ballSkinURL === "" ? {fillStyle: "white"} : {sprite: {texture: ballSkinURL, xScale: 0.2, yScale: 0.2}};
    if (ballValue > 0 && ballValue * 100 % 1 == 0) {
        const xhr = window.XMLHttpRequest ? new XMLHttpRequest : new ActiveXObject("Microsoft.XMLHTTP");
        xhr.open("POST", "/drop_ball", true);
        xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        xhr.responseType = "text";
        xhr.onload = function() {
            if (xhr.status === 200) {
                if (!isNaN(parseFloat(xhr.responseText))) {
                    var newBall = Bodies.circle(425, 0, 5, {label: "plinkoball", friction: 0, restitution: 0.2, render: renderProperties, value: ballValue});
                    Composite.add(engine.world, [newBall]);
                    refLamCoinText.innerHTML = parseFloat(xhr.responseText) % 1 === 0 ? parseInt(xhr.responseText) : parseFloat(xhr.responseText);
                }
                else if (xhr.responseText !== "insufficient funds") {
                    alert("An error occurred. Please try again later.");
                }
            } else {
                alert("An error occurred. Please try again later.");
            }
        }
        var request = new URLSearchParams({
            ballvalue: ballValue
        });
        xhr.send(request.toString());
    }
});

Events.on(engine, "collisionStart", function(event) {
    var collidingPair = event.pairs;
    for (let pair of collidingPair) {
        var collidedBucket = null;
        var collidedBall = null;
        var multiplierValue =  null;
        var ballValue = null;
        var bodies = [pair.bodyA, pair.bodyB]
        for (let body of bodies) {
            if (body.label === "bucket") {
                collidedBucket = body;
                multiplierValue = body.value;
            }
            else if (body.label === "plinkoball") {
                collidedBall = body;
                ballValue = body.value;
            }
            else if (body.label === "peg") {
                let randomNum = Math.floor(Math.random() * 4);
                document.querySelectorAll(".boingsound")[randomNum].play();
            }
            if (collidedBall != null && collidedBucket != null) {
                World.remove(engine.world, collidedBall);
                plinkoBalls.splice(plinkoBalls.indexOf(collidedBall));
                const xhr = window.XMLHttpRequest ? new XMLHttpRequest : new ActiveXObject("Microsoft.XMLHTTP");
                xhr.open("POST", "/receive_ball", true);
                xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
                xhr.responseType = "text";
                xhr.onload = function() {
                    if (xhr.status === 200) {
                        if (!isNaN(parseFloat(xhr.responseText))) {
                            refLamCoinText.innerHTML = parseFloat(xhr.responseText) % 1 === 0 ? parseInt(xhr.responseText) : parseFloat(xhr.responseText);
                        }
                        else {
                            alert("An error occurred. Please try again later.");
                        }
                    } else {
                        alert("An error occurred. Please try again later.");
                    }
                }
                var request = new URLSearchParams({
                    ballvalue: ballValue,
                    multiplier: multiplierValue
                });
                xhr.send(request.toString());
            }
        }
    }
});

Render.run(render);
var runner = Runner.create();
Runner.run(runner, engine);