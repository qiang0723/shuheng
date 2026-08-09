import path from "node:path";
import { fileURLToPath } from "node:url";

import { startProdServer } from "./vinext/dist/server/prod-server.js";

const root = path.dirname(fileURLToPath(import.meta.url));
const port = Number(process.env.PORT ?? "3000");
const host = process.env.HOST ?? "0.0.0.0";

if (!Number.isInteger(port) || port < 1 || port > 65535) {
  throw new Error(`invalid PORT: ${process.env.PORT}`);
}

await startProdServer({
  host,
  port,
  outDir: path.join(root, "dist"),
});
