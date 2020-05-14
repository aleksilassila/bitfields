import React from "react";

class Home extends React.Component {
    componentDidMount() {
        const ws = new WebSocket("ws://" + window.location.hostname + ":8765");

        const startGame = () => {
            let move = [0, 0, 0, 0]; // w, d, s, a
            let shoot = false;
            let map = [];

            const c = document.getElementById("game");
            const ctx = c.getContext("2d");

            const sendData = () => {
                let moveDir = null;
                const payload = {};

                if (move[0]) {
                    moveDir = 0;
                } else if (move[1]) {
                    moveDir = 1;
                } else if (move[2]) {
                    moveDir = 2;
                } else if (move[3]) {
                    moveDir = 3;
                }

                if (moveDir !== null) {
                    payload.m = moveDir;
                }

                if (shoot) {
                    payload.s = true;
                }

                shoot = null;
                moveDir = null;

                payload !== {} ? ws.send(JSON.stringify(payload)) : null;
            };

            ws.onmessage = (m) => {
                const action = JSON.parse(m.data);
                const floor = action.f;

                if ("map" in action) {
                    map = action.map;
                    return;
                }

                // Copy temp map to print
                let mapToPrint = [];
                for (let i = 0; i < map[floor].length; i++) {
                    mapToPrint[i] = [...map[floor][i]];
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
                    move = [0, 0, 0, 0];
                    move[0] = 1;
                } else if (e.key.toLowerCase() === "d") {
                    move = [0, 0, 0, 0];
                    move[1] = 1;
                } else if (e.key.toLowerCase() === "s") {
                    move = [0, 0, 0, 0];
                    move[2] = 1;
                } else if (e.key.toLowerCase() === "a") {
                    move = [0, 0, 0, 0];
                    move[3] = 1;
                } else if (e.code === "Space") {
                    shoot = true;
                }
            };

            document.onkeyup = (e) => {
                if (e.key.toLowerCase() === "w") {
                    move[0] = 0;
                } else if (e.key.toLowerCase() === "d") {
                    move[1] = 0;
                } else if (e.key.toLowerCase() === "s") {
                    move[2] = 0;
                } else if (e.key.toLowerCase() === "a") {
                    move[3] = 0;
                }
            };
        };

        ws.onopen = () => startGame();
    }

    render() {
        return (
            <div className="container">
                <canvas id="game"></canvas>
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

                        color: lime;
                        font-size: 1em;
                        font-family: "Roboto mono", monospace;
                        line-height: 0.9em;
                        white-space: pre;
                        text-shadow: 0px 0px 3px lime;
                    }

                    .container {
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        width: 100vw;
                    }

                    #game {
                    }

                    .red {
                        color: red;
                        text-shadow: 0px 0px 3px red;
                    }

                    .orange {
                        color: orange;
                        text-shadow: 0 0 3px orange;
                    }

                    .white {
                        color: white;
                        text-shadow: 0px 0px 3px white;
                    }
                `}</style>
            </div>
        );
    }
}

export default Home;
