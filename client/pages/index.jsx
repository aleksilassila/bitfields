import { useState, useEffect } from "react";

const Home = () => {
    const [name, setName] = useState("");
    const [scores, setScores] = useState({});
    const [playerId, setPlayerId] = useState(false);

    const connect = () => {
        console.log("Connecting...");
        const ws = new WebSocket("ws://" + window.location.hostname + ":8765");

        const shakeHands = () => {
            ws.send(JSON.stringify({ name }));
        };

        const startGame = () => {
            document.getElementById("start-game").style.display = "none";
            document.getElementById("game-container").style.display = "flex";

            shakeHands();

            let move = false; // w, d, s, a
            let shoot = false;
            let doAction = false;
            let fortify = false;
            let map = shakeHands();

            document
                .getElementById("fortify-button")
                .addEventListener("click", () => {
                    fortify = true;
                });

            const c = document.getElementById("game");
            const ctx = c.getContext("2d");

            const sendData = () => {
                const payload = {};

                if (move !== false) {
                    payload.m = move;
                }

                if (shoot) {
                    payload.s = true;
                }

                if (doAction) {
                    payload.a = true;
                    doAction = false;
                }

                if (fortify) {
                    payload.f = true;
                    fortify = false;
                }

                payload !== {} ? ws.send(JSON.stringify(payload)) : null;
            };

            ws.onmessage = (m) => {
                if (m.data[0] === "s") {
                    setScores(JSON.parse(m.data.substr(1)));
                    return;
                }

                const action = JSON.parse(m.data);
                const floor = action.f;

                if ("map" in action) {
                    map = action.map;
                    setPlayerId(action.playerId);
                    return;
                }

                // Apply updates to map
                for (let key in action.u) {
                    const pos = action.u[key].p;

                    map[pos[2]][pos[1]][pos[0]] = action.u[key].c;
                }

                // Copy temp map to print
                let mapToPrint = [];
                for (let i = 0; i < map[floor].length; i++) {
                    mapToPrint[i] = [...map[floor][i]];
                }

                // Render geysers
                for (let key in action.g) {
                    for (let key in action.g) {
                        const pos = action.g[key].p;

                        if (action.g[key].s === 2) {
                            mapToPrint[pos[1]][pos[0]] = "2";
                        } else if (action.g[key].s === 1) {
                            mapToPrint[pos[1]][pos[0]] = "1";
                        } else {
                            mapToPrint[pos[1]][pos[0]] = "0";
                        }
                    }
                }

                // Render players
                for (let key in action.p) {
                    if (
                        action.p[key].p[0] !== null &&
                        action.p[key].f === action.f
                    ) {
                        const pos = action.p[key].p;
                        mapToPrint[pos[1]][pos[0]] =
                            key === action.i.toString() ? "&" : "@";
                    }
                }

                // Bullets
                if (action.b && !(action.b === {})) {
                    for (let key in action.b) {
                        const pos = action.b[key].p;

                        if (action.b[key].f === action.f) {
                            mapToPrint[pos[1]][pos[0]] = "•";
                        }
                    }
                }

                const windowSize = [
                    action.f === 0 ? 31 : 61,
                    action.f === 0 ? 19 : 39,
                ];

                const w = windowSize[0] * 8;
                const h = windowSize[1] * 10;

                c.width = 2 * w;
                c.height = 2 * h;
                c.style.width = w + "px";
                c.style.height = h + "px";
                ctx.clearRect(0, 0, c.width, c.height);
                ctx.font = "10px Roboto Mono";
                ctx.shadowOffsetX = 0;
                ctx.shadowOffsetY = 0;
                ctx.shadowBlur = 10;
                ctx.scale(2, 2);

                const offset = {
                    left:
                        action.p[action.i].p[0] - Math.floor(windowSize[0] / 2),
                    top:
                        action.p[action.i].p[1] - Math.floor(windowSize[1] / 2),
                };

                for (
                    let rIndex = // Starting index for rows, increments window
                            offset.top > 0 // height times to loop rows
                                ? offset.top + windowSize[1] > mapToPrint.length
                                    ? mapToPrint.length - windowSize[1]
                                    : offset.top
                                : 0,
                        rInitial = rIndex;
                    rIndex < rInitial + windowSize[1];
                    rIndex++
                ) {
                    for (
                        let cIndex =
                                offset.left > 0
                                    ? offset.left + windowSize[0] >
                                      mapToPrint[rIndex].length
                                        ? mapToPrint[rIndex].length -
                                          windowSize[0]
                                        : offset.left
                                    : 0,
                            cInitial = cIndex;
                        cIndex < cInitial + windowSize[0];
                        cIndex++
                    ) {
                        let character = mapToPrint[rIndex][cIndex];
                        if (character === "&") {
                            ctx.fillStyle = "white";
                            ctx.shadowColor = "white";
                        } else if (character === "@" || character === "•") {
                            ctx.fillStyle = "red";
                            ctx.shadowColor = "red";
                        } else if (character === "_" || character === ".") {
                            ctx.fillStyle = "orange";
                            ctx.shadowColor = "orange";
                        } else if (character === "2") {
                            ctx.fillStyle = "deeppink";
                            ctx.shadowColor = "deeppink";
                            character = "M";
                        } else if (character === "1") {
                            ctx.fillStyle = "blueviolet";
                            ctx.shadowColor = "blueviolet";
                            character = "M";
                        } else if (character === "0") {
                            ctx.fillStyle = "gold";
                            ctx.shadowColor = "gold";
                            character = "M";
                        } else {
                            ctx.fillStyle = "lime";
                            ctx.shadowColor = "lime";
                        }

                        ctx.fillText(
                            character,
                            8 * (cIndex - cInitial),
                            10 + 10 * (rIndex - rInitial)
                        );
                    }
                }

                sendData();
            };

            document.onkeydown = (e) => {
                if (e.key.toLowerCase() === "w") {
                    move = 0;
                } else if (e.key.toLowerCase() === "d") {
                    move = 1;
                } else if (e.key.toLowerCase() === "s") {
                    move = 2;
                } else if (e.key.toLowerCase() === "a") {
                    move = 3;
                } else if (e.code === "Space") {
                    shoot = true;
                } else if (e.key.toLowerCase() === "e") {
                    doAction = true;
                }
            };

            document.onkeyup = (e) => {
                if (e.key.toLowerCase() === "w" && move === 0) {
                    move = false;
                } else if (e.key.toLowerCase() === "d" && move === 1) {
                    move = false;
                } else if (e.key.toLowerCase() === "s" && move === 2) {
                    move = false;
                } else if (e.key.toLowerCase() === "a" && move === 3) {
                    move = false;
                } else if (e.code === "Space") {
                    shoot = false;
                }
            };
        };

        ws.onopen = () => startGame();
    };

    return (
        <div className="container">
            <div id="start-game">
                <h1>Bitfields</h1>
                <div id="inputs">
                    <input
                        id="name-field"
                        type="text"
                        placeholder="Nickname"
                        value={name}
                        onChange={(e) => {
                            e.target.value.length <= 20 &&
                                setName(e.target.value);
                        }}
                    />
                    <input
                        className="button"
                        type="button"
                        value="Play"
                        onClick={(e) => {
                            connect();
                        }}
                    />
                </div>
            </div>
            <div id="game-container">
                <div id="toolbar">
                    <input
                        className="button"
                        id="fortify-button"
                        type="button"
                        value="Fortify"
                    />
                </div>
                <canvas id="game"></canvas>
                <div id="highscores">
                    <h2>Leaderboard</h2>
                    <ul>
                        {Object.keys(scores).map((key, index) => {
                            if (index < 5) {
                                return (
                                    <li key={index}>
                                        {scores[key].n}: {scores[key].s}
                                    </li>
                                );
                            }
                        })}
                    </ul>
                    <h2>Your stats</h2>
                    {scores[playerId] ? (
                        <ul>
                            <li>Score: {scores[playerId].s}</li>
                            <li>Money: {scores[playerId].m}</li>
                        </ul>
                    ) : null}
                </div>
            </div>
            <link
                href="https://fonts.googleapis.com/css?family=Roboto+Mono&display=swap"
                rel="stylesheet"
            />
            <style jsx global>{`
                html,
                body {
                    margin: 0;
                    padding: 0;
                    background-color: #000;
                    background: radial-gradient(
                        circle,
                        rgba(15, 30, 30, 1) 30%,
                        rgba(0, 0, 0, 1) 100%
                    );

                    font-family: "Roboto mono", monospace;
                    color: lime;
                    text-shadow: 0px 0px 3px lime;
                }

                .container {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    width: 100vw;
                }

                #start-game {
                    width: 60vw;
                    display: flex;
                    justify-content: center;
                    flex-direction: column;
                }

                #start-game h1 {
                    font-size: 4em;
                    margin: 0;
                    text-align: center;
                    margin-bottom: 1em;
                }

                #inputs  {
                    display: flex;
                }

                #name-field {
                    font-family: "Roboto mono", monospace;
                    border-radius: 2px;
                    outline: none;
                    color: lime;
                    text-shadow: 0 0 3px lime;
                    padding: 0.5rem 1rem;
                    background: none;

                    border: 2px solid #00ff00;
                    box-shadow: 0 0 5px 0px lime;

                    flex: 1 0 auto;
                }

                .button {
                    font-family: "Roboto mono", monospace;

                    border-radius: 2px;
                    outline: none;
                    background: none;

                    cursor: pointer;

                    color: lime;
                    text-shadow: 0 0 3px lime;
                    border: 2px solid #00ff00;
                    box-shadow: 0 0 5px 0px lime;

                    padding: 0.5rem 1rem;
                    margin-left: 1em;
                }

                #toolbar {
                    display: flex;
                    flex-direction: column;
                    margin-right: 2em;
                    padding: 0.83em 0;
                }

                #fortify-button {
                    color: #000000;
                    text-shadow: 0 0 3px #000;
                    background-color: lime;
                    margin: 0;
                }

                #game-container {
                    display: none;
                }

                #highscores  {
                    margin-left: 2em;
                }

                ul {
                    list-style-type: none;
                    padding-left: 1em;
                }

                ::placeholder {
                    color: lime;
                    opacity: 0.4;
                }
            `}</style>
        </div>
    );
};

export default Home;
