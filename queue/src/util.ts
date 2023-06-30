import { Event as NostrEvent } from "nostr-tools";
import { CLEAN_YT_URL, VIDEO_ID_REGEX, YT_OEMBED_URL } from "~/config";
import { VideoData, Video, YtVideoData } from "~/types";

const parseZapReceipt = async (note: NostrEvent): Promise<Video | null> => {
  const zapRequest = note.tags.find((t) => t[0] === "description");
  if (!zapRequest || !zapRequest[1]) return null;

  try {
    const request: NostrEvent = JSON.parse(zapRequest[1]);

    const amountTag = request.tags.find((t) => t[0] === "amount");
    if (!amountTag || !amountTag[1]) return null;
    const amount = parseInt(amountTag[1]) / 1000;

    const videoId = parseVideoIdFromContent(request.content);
    if (!videoId) return null;

    const videoData = await queryVideo(videoId);
    if (!videoData) return null;
    return {
      ...videoData,
      amount: amount,
    };
  } catch (e) {
    console.error("Invalid zap request event");
  }

  return null;
};

const parseVideoIdFromContent = (content: string): string | null => {
  if (content === "") return null;

  const parsedUrl = VIDEO_ID_REGEX.exec(content);
  if (!parsedUrl || !parsedUrl[2]) return null;

  return parsedUrl[2];
};

export const queryVideo = async (
  videoId: string
): Promise<VideoData | null> => {
  const query =
    YT_OEMBED_URL + encodeURIComponent(`${CLEAN_YT_URL}${videoId}&format=json`);
  const res: YtVideoData = await fetch(query)
    .then((res) => res.json())
    .catch((err) => {
      console.error("Error fetching YT video data", err.message);
    });

  return {
    author: res.author_name,
    thumbnail: res.thumbnail_url,
    title: res.title,
    videoId: videoId,
  };
};

export { parseZapReceipt, parseVideoIdFromContent };
