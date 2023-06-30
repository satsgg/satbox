import { Video } from "~/types";

let queue: Video[] = [];

const insertQueue = (video: Video) => {
  const existingVideo = queue.find((v) => v.videoId === video.videoId);
  if (existingVideo) {
    existingVideo.amount += video.amount;
  } else {
    queue.push(video);
  }

  queue.sort((a, b) => b.amount - a.amount);
  console.debug("queue", queue);
  return;
};

const next = () => {
  if (!queue[0]) return null;
  return queue[0];
};

const nextPop = () => {
  if (!queue[0]) return null;
  const next = queue[0];
  queue.shift();
  return next;
};

export { queue, insertQueue, next, nextPop };
