# Bitfields Client

Based on Next.js.

## Getting started

Install required packages using `yarn install (npm install)`. To start a development server, use `yarn dev (npm run dev)`.

## Production

For production, build the app using `yarn build (npm run build)` and then `yarn start (npm start)`.

### Nginx and external game server

-   next.config.js

`module.exports = { env: { serverAddress: "ip of game server", }, assetPrefix: '/bitfields', };`

assetPrefix because of nginx

-   pages/index.jsx -> pages/bitfields/index.jsx

### Environment variables

If you would like to specify different game server address, you can do it in the `next.config.js` file.
