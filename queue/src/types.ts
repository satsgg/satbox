type VideoData = {
  author: string;
  thumbnail: string;
  title: string;
  videoId: string;
};

type Video = VideoData & {
  amount: number;
};

type YtVideoData = {
  title: string;
  author_name: string;
  author_url: string;
  type: string;
  height: number;
  width: number;
  version: string;
  provider_name: string;
  provider_url: string;
  thumbnail_height: number;
  thumbnail_width: number;
  thumbnail_url: string;
  html: string;
};

export { type VideoData, type Video, type YtVideoData };
