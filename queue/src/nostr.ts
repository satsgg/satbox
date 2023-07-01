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
        "8756779be69455fee07957ae409a7485914b06a747ff0b105721dcf1538697e1",
      ],
      "#e": [
        "a7e2183c808b767afdd174a770cab76190dfd9dd0f328862c0456b8dcf36cfce",
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
