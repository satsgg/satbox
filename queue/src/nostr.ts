import "websocket-polyfill";
import { SimplePool, Event as NostrEvent } from "nostr-tools";
import { insertQueue } from "~/store";
import { parseZapReceipt } from "~/util";
import { DEFAULT_RELAYS } from "~/config";

const initializeNostr = () => {
  const pool = new SimplePool();
  const now = Math.floor(Date.now() / 1000);
  let sub = pool.sub(DEFAULT_RELAYS, [
    {
      kinds: [9735],
      since: now,
      "#p": [
        "e9038e10916d910869db66f3c9a1f41535967308b47ce3136c98f1a6a22a6150",
      ],
    },
  ]);

  sub.on("event", async (event: NostrEvent) => {
    const video = await parseZapReceipt(event);
    if (!video) return;
    insertQueue(video);
  });
};
export { initializeNostr };
