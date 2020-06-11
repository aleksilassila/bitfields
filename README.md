# Bitfields

Explore procedurally generated maps with other players, build bases and fight others in your web browser!

My latest project, a text-based .io style game powered by python, websockets and javascript canvas. Supports multiplayer and custom procedural map generation using simplex noise.

[Live demo!](http://ec2-3-87-232-152.compute-1.amazonaws.com/bitfields)

## To get started:

### Create a server:

Inside `bitfields/server`:

-   Make sure you have at least python3.7 installed.

-   `pip3 install -r requirements.txt`

-   Tweak `config.py` if necessary

-   `python3 main.py`

### Set up frontend client

Inside `bitfields/client`:

-   Run `yarn install` `(npm install)`

-   Start development server: `yarn dev` `(npm run dev)`

Next head to [localhost:3000](http://localhost:3000)

OR alternatively export frontend as static web page for serverless use:

Inside `bitfields/client`: `yarn export` `(npm run export)`

## Screenshots

![](screenshot1.png?raw=true "Welcome to the Bitfields!")
![](screenshot2.png?raw=true "Potentially endless procedural worlds!")
![](screenshot3.png?raw=true "Underworld cave system with limited visibility ^^")

## To Do

-   Spawn points
-   Reduce amount of loops: make more efficient
-   Cave rooms / systems
-   Breach ammunition? Mines?
-   Announce kills / deaths
-   Teams?
-   Place ladders?

## Bugs

-   Double clicking connect / play creates 2 players
