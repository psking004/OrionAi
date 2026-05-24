import express, { type Express } from "express";
import cors from "cors";
import pinoHttp from "pino-http";
import router from "./routes";
import { logger } from "./lib/logger";

const app: Express = express();

app.use(
  pinoHttp({
    logger,
    serializers: {
      req(req) {
        return {
          id: req.id,
          method: req.method,
          url: req.url?.split("?")[0],
        };
      },
      res(res) {
        return {
          statusCode: res.statusCode,
        };
      },
    },
  }),
);
app.use(cors({ origin: "*", credentials: false }));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ── FastAPI transparent proxy ──────────────────────────────────────────────────
// The generated client calls /api/<path>. The FastAPI backend serves at
// /api/v1/<path>. This proxy intercepts non-internal routes and rewrites them.
//
// /api/auth/...      → http://localhost:8000/api/v1/auth/...
// /api/projects/...  → http://localhost:8000/api/v1/projects/...
//
// /api/healthz is kept local (served by the api-server itself).

const FASTAPI_BASE = "http://localhost:8000";
const SKIP_REQ_HEADERS = new Set(["host", "connection", "transfer-encoding", "content-length"]);
const SKIP_RES_HEADERS = new Set(["transfer-encoding", "connection", "keep-alive"]);
const FASTAPI_PATHS = /^\/api\/(auth|projects)(\/|$)/;

async function proxyToFastApi(
  req: express.Request,
  res: express.Response,
  targetPath: string,
): Promise<void> {
  try {
    // Rebuild query string
    const qs = req.originalUrl.includes("?") ? req.originalUrl.slice(req.originalUrl.indexOf("?")) : "";
    const target = `${FASTAPI_BASE}${targetPath}${qs}`;

    const forwardHeaders: Record<string, string> = {};
    for (const [k, v] of Object.entries(req.headers)) {
      if (!SKIP_REQ_HEADERS.has(k.toLowerCase()) && typeof v === "string") {
        forwardHeaders[k] = v;
      }
    }

    const hasBody = !["GET", "HEAD", "DELETE", "OPTIONS"].includes(req.method.toUpperCase());
    const body = hasBody && req.body !== undefined ? JSON.stringify(req.body) : undefined;
    if (body !== undefined) {
      forwardHeaders["content-type"] = "application/json";
    }

    const response = await fetch(target, {
      method: req.method,
      headers: forwardHeaders,
      body,
    });

    res.status(response.status);
    for (const [k, v] of response.headers.entries()) {
      if (!SKIP_RES_HEADERS.has(k.toLowerCase())) {
        res.setHeader(k, v);
      }
    }

    const text = await response.text();
    res.send(text);
  } catch (err) {
    logger.error({ err }, "FastAPI proxy error");
    res.status(502).json({ detail: "FastAPI backend unavailable" });
  }
}

// Route: /api/auth/* and /api/projects/* → FastAPI at /api/v1/*
app.all(FASTAPI_PATHS, (req, res) => {
  // req.originalUrl = /api/auth/login  →  targetPath = /api/v1/auth/login
  const targetPath = req.originalUrl
    .replace(/\?.*$/, "")        // strip query string (added back in proxyToFastApi)
    .replace(/^\/api\//, "/api/v1/"); // /api/X → /api/v1/X
  void proxyToFastApi(req, res, targetPath);
});

// ── Existing routes ────────────────────────────────────────────────────────────
app.use("/api", router);

export default app;
