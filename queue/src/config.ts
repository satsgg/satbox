const VIDEO_ID_REGEX = /(watch\?v=)?([\w\-\d]{11})/;
const CLEAN_YT_URL = "https://www.youtube.com/watch?v=";
const YT_OEMBED_URL = "https://www.youtube.com/oembed?url=";

const DEFAULT_RELAYS = [
  "wss://brb.io",
  "wss://relay.damus.io",
  "wss://nostr.fmt.wiz.biz",
  "wss://nostr.oxtr.dev",
  "wss://arc1.arcadelabs.co",
  "wss://relay.nostr.ch",
  "wss://eden.nostr.land",
  "wss://nos.lol",
  "wss://relay.snort.social",
  "wss://relay.current.fyi",
];

export { VIDEO_ID_REGEX, CLEAN_YT_URL, YT_OEMBED_URL, DEFAULT_RELAYS };
