# Bitfields

Explore procedurally generated maps with other players, build bases and fight others in your web browser!

My latest project, a text-based .io style game powered by python, websockets and javascript canvas. Supports multiplayer and custom procedural map generation using simplex noise.

## This project is currently WORK IN PROGRESS!

## To get started:

-   Create a server inside `bitfields/server`: `python3 main.py`

-   Inside `bitfields/client` run `yarn install` `(npm install)`

-   Start frontend inside `bitfields/client`: `yarn dev` `(npm run dev)`

-   Head to [localhost:3000](http://localhost:3000)

OR alternatively export frontend as static web page for serverless use:

-   Inside `bitfields/client`: `yarn export` `(npm run export)`

Live demo upcoming later...

## Screenshots

![](screenshot1.png?raw=true "Welcome to the Bitfields!")
![](screenshot2.png?raw=true "Potentially endless procedural worlds!")
![](screenshot3.png?raw=true "Underworld cave system with limited visibility ^^")

## To Do

-   Spawn points
-   _Chunks and NPCs_
-   Reduce amount of loops: make more efficient
-   Action queue: better "anticheat"
-   Teams?
-   Place ladders?
