import { useState, useEffect } from "react";

import Help from "../containers/Help";
import Button from "../components/Button";
import RoundButton from "../components/RoundButton";

const Home = () => {
    const [name, setName] = useState("");
    const [scores, setScores] = useState({});
    const [playerId, setPlayerId] = useState(false);
    const [currentFloor, setCurrentFloor] = useState(1);

    const [showHelp, setShowHelp] = useState(false);

    const connect = () => {
        console.log("Connecting...");
        const ws = new WebSocket("ws://" + window.location.hostname + ":8765");

        const startGame = () => {
            document.getElementById("start-game").style.display = "none";
            document.getElementById("game-container").style.display = "flex";

            let move = false; // w, d, s, a
            let shoot = false;
            let doAction = false;

            let fortify = false;
            let door = false;

            let map;

            // document
            //     .getElementById("fortify-button")
            //     .addEventListener("click", () => {
            //         document.activeElement.blur();
            //         fortify = true;
            //     });

            // document
            //     .getElementById("door-button")
            //     .addEventListener("click", () => {
            //         document.activeElement.blur();
            //         door = true;
            //     });

            const c = document.getElementById("game");
            const ctx = c.getContext("2d");

            const shakeHands = (data) => {
                setPlayerId(data.playerId);
                map = data.map;
            };

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

                if (door) {
                    payload.d = true;
                    door = false;
                }

                payload !== {} ? ws.send(JSON.stringify(payload)) : null;
            };

            const doAnimation = async (data) => {
                const animation = data.a;
                const pos = data.p;
                const floor = data.f;

                const character = map[floor][pos[1]][pos[0]];

                // If animation is blink
                if (animation === "b") {
                    map[floor][pos[1]][pos[0]] = " ";
                    await new Promise((r) => setTimeout(r, 200));
                    map[floor][pos[1]][pos[0]] = character;
                }
            };

            // Begin the handshake
            ws.send(JSON.stringify({ name }));

            ws.onmessage = (m) => {
                if (m.data[0] === "s") {
                    setScores(JSON.parse(m.data.substr(1)));
                    return;
                }

                if (m.data[0] === "a") {
                    doAnimation(JSON.parse(m.data.substr(1)));
                    return;
                }

                const action = JSON.parse(m.data);
                const floor = action.f;
                setCurrentFloor(floor);

                if (map === undefined && "map" in action) {
                    shakeHands(action);
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
                    const pos = action.g[key].p;

                    if (action.g[key].f === floor) {
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
                } else if (e.key.toLowerCase() === "f") {
                    fortify = true;
                } else if (e.key.toLowerCase() === "g") {
                    door = true;
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
            <Help visible={showHelp} setVisible={setShowHelp} />
            <div id="start-game">
                <h1 id="title">Bitfields</h1>
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
                    <Button
                        value="Play"
                        id="play-button"
                        onClick={(e) => {
                            connect();
                        }}
                    />
                </div>
            </div>
            <RoundButton
                id="help-button"
                onClick={() => setShowHelp(true)}
                value="?"
            />
            <div id="game-container">
                {/*                <div id="toolbar">
                    <Button
                        id="fortify-button"
                        className="toolbar-button"
                        value="Fortify $300"
                    />
                    <Button
                        id="door-button"
                        className="toolbar-button"
                        value="Door $1000"
                    />
                </div>*/}
                <div id="game-wrapper">
                    <canvas id="game"></canvas>
                    <div id="toolbar">
                        <span id="toolbar-name">
                            Name:{" "}
                            <span className="stats-color">
                                {scores[playerId] ? scores[playerId].n : null}
                            </span>
                        </span>
                        {currentFloor ? (
                            <span id="toolbar-score">
                                Score:{" "}
                                <span className="stats-color">
                                    {scores[playerId]
                                        ? scores[playerId].s
                                        : null}
                                </span>
                            </span>
                        ) : null}
                        <span id="toolbar-money">
                            Money:{" "}
                            <span className="stats-color">
                                {scores[playerId] ? scores[playerId].m : null}
                            </span>
                        </span>
                        <span id="toolbar-health">
                            Health:{" "}
                            <span className="stats-color">
                                {scores[playerId] ? scores[playerId].h : null}
                            </span>
                        </span>
                        {currentFloor ? (
                            <span id="toolbar-position">
                                Position:{" "}
                                <span className="stats-color">
                                    {scores[playerId]
                                        ? `${scores[playerId].p[0]}, ${scores[playerId].p[1]}`
                                        : null}
                                </span>
                            </span>
                        ) : null}
                    </div>
                </div>
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
                    {/*                    <h2>Your stats</h2>
                    {scores[playerId] ? (
                        <ul>
                            <li>Score: {scores[playerId].s}</li>
                            <li>Money: {scores[playerId].m}</li>
                        </ul>
                    ) : null}*/}
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

                html {
                    background-color: #020303;
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
                    margin-bottom: 0.2em;
                }

                #inputs  {
                    display: flex;
                    justify-content: center;
                }

                #name-field {
                    font-family: "Roboto mono", monospace;
                    border-radius: 2px;
                    outline: none;
                    color: lime;
                    text-shadow: 0 0 3px lime;
                    padding: 0.5rem 1rem;
                    background: none;

                    max-width: 200px;

                    border: 2px solid #00ff00;
                    box-shadow: 0 0 5px 0px lime;

                    flex: 1 0 auto;
                }

                 {
                    /*                #toolbar {
                    display: flex;
                    flex-direction: column;
                    margin-right: 2em;
                    padding: 0.83em 0;
                }*/
                }

                #toolbar {
                    display: flex;
                    flex-direction: row;
                    font-size: 10px;
                }

                #toolbar-name,
                #toolbar-score,
                #toolbar-money,
                #toolbar-health {
                    margin-right: 1em;
                }

                #toolbar-position {
                    margin-left: auto;
                }

                #play-button  {
                    margin-left: 1em;
                }

                .toolbar-button input {
                    color: #000000 !important;
                    text-shadow: 0 0 3px #000 !important;
                    background-color: lime !important;
                    margin: 0;
                    margin-bottom: 1em;
                    width: 100%;
                }

                #game-container {
                    display: none;
                }

                #highscores  {
                    margin-left: 2em;
                    min-width: 300px;
                }

                #help-button {
                    position: absolute;
                    top: 1em;
                    right: 1em;
                }

                ul {
                    list-style-type: none;
                    padding-left: 1em;
                }

                ::placeholder {
                    color: lime;
                    opacity: 0.4;
                }

                .stats-color {
                    color: mediumspringgreen;
                    text-shadow: 0px 0px 3px mediumspringgreen;
                }

                button {
                    cursor: pointer;
                }
            `}</style>
        </div>
    );
};

export default Home;
