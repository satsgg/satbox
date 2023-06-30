import express from "express";
import "websocket-polyfill";
import { parseVideoIdFromContent, queryVideo } from "~/util";
import { Video } from "~/types";
import { insertQueue, next, nextPop, queue } from "~/store";
import { initializeNostr } from "~/nostr";

initializeNostr();

const app: express.Application = express();
app.use(express.json());
const port: number = 5000;

app.get("/queue", (req, res) => {
  res.send(queue);
});

app.get("/next", async (req, res) => {
  const shouldPop = req.query.pop && req.query.pop == "true" ? true : false;
  const nextVideo = shouldPop ? nextPop() : next();

  res.json(nextVideo);
});

// test endpoint
app.post("/video", async (req, res) => {
  const content: string = req.body.content;
  const amount: number = req.body.amount;
  const videoId = parseVideoIdFromContent(content);
  if (!videoId) return null;

  const videoData = await queryVideo(videoId);
  if (!videoData) return null;
  const video: Video = {
    ...videoData,
    amount: amount,
  };
  insertQueue(video);
  res.send(video);
});

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`);
});
