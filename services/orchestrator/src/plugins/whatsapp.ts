// WhatsApp plugin backed by Baileys (no headless browser needed).
// Pairing: call GET /wa/qr while a QR is pending and scan it from the
// phone that owns the session; session persists in WA_SESSION_DIR.
import fastifyPlugin from 'fastify-plugin';
import makeWASocket, {
  useMultiFileAuthState,
  fetchLatestBaileysVersion,
  DisconnectReason,
} from '@whiskeysockets/baileys';
import QRCode from 'qrcode';
import fs from 'node:fs';
import type { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';

export type WaStatus = 'disconnected' | 'connecting' | 'connected';

export interface WaEventEmitter {
  on(event: string, listener: (...args: unknown[]) => void): void;
  removeAllListeners(event?: string): void;
}

export interface WaSocketLike {
  ev: WaEventEmitter;
  sendMessage(jid: string, content: { text: string }): Promise<unknown>;
  logout(): Promise<void>;
  end(error: Error | undefined): void;
}

export interface WhatsappDependencies {
  useMultiFileAuthState: (
    folder: string,
  ) => Promise<{ state: unknown; saveCreds: () => Promise<void> }>;
  fetchLatestBaileysVersion: () => Promise<{ version: [number, number, number] }>;
  makeWASocket: (config: {
    version: [number, number, number];
    auth: unknown;
    printQRInTerminal: boolean;
  }) => WaSocketLike;
  qrToDataUrl: (text: string) => Promise<string>;
  querySidra?: (query: string, sessionId: string) => Promise<string>;
}

export interface WhatsappPluginOptions {
  sessionDir?: string;
  autoConnect?: boolean;
  initialReconnectDelayMs?: number;
  maxReconnectDelayMs?: number;
  maxReconnectAttempts?: number;
  random?: () => number;
  deps?: Partial<WhatsappDependencies>;
}

interface BaileysDisconnectError {
  output?: { statusCode?: number };
}

interface BaileysConnectionUpdate {
  connection?: string;
  lastDisconnect?: { error?: BaileysDisconnectError | Error };
  qr?: string;
}

interface SendBody {
  to: string;
  message: string;
}

const EXPLICIT_USER_JID_RE = /^[1-9]\d{7,14}@s\.whatsapp\.net$/;
const PHONE_ALLOWED_CHARS_RE = /^[+\d\s().-]+$/;
const PHONE_DIGITS_RE = /^[1-9]\d{7,14}$/;
const MAX_MESSAGE_LENGTH = 4096;
const DEFAULT_INITIAL_RECONNECT_DELAY_MS = 2000;
const DEFAULT_MAX_RECONNECT_DELAY_MS = 60000;
const DEFAULT_MAX_RECONNECT_ATTEMPTS = 8;

const defaultDependencies: WhatsappDependencies = {
  useMultiFileAuthState: (folder) => useMultiFileAuthState(folder),
  fetchLatestBaileysVersion: () => fetchLatestBaileysVersion(),
  makeWASocket: (config) =>
    makeWASocket(config as Parameters<typeof makeWASocket>[0]) as unknown as WaSocketLike,
  qrToDataUrl: (text) => QRCode.toDataURL(text),
  querySidra: async (query: string, sessionId: string): Promise<string> => {
    const sidraUrl = process.env.FLECTRA_SIDRA_URL || 'http://flectra:8069/sidra/api/query';
    const token = process.env.ORCHESTRATOR_TOKEN || '';
    const resp = await fetch(sidraUrl, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-orchestrator-token': token,
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'call',
        params: { query, session_id: sessionId, limit: 3 },
      }),
    });
    if (!resp.ok) {
      throw new Error(`Sidra API HTTP ${resp.status}`);
    }
    const payload = (await resp.json()) as { result?: { ok?: boolean; answer?: string } };
    return payload.result?.answer || 'Tidak ditemukan rujukan dalam korpus MoonWitness Sidra.';
  },
};

export function normalizeWhatsAppRecipient(rawRecipient: string): string | null {
  const trimmed = rawRecipient.trim();
  if (!trimmed) return null;

  if (trimmed.includes('@')) {
    return EXPLICIT_USER_JID_RE.test(trimmed) ? trimmed : null;
  }

  if (!PHONE_ALLOWED_CHARS_RE.test(trimmed)) {
    return null;
  }

  const plusMatches = trimmed.match(/\+/g);
  if (plusMatches && (plusMatches.length > 1 || /\d.*\+/.test(trimmed))) {
    return null;
  }

  const digits = trimmed.replace(/[+\s().-]/g, '');
  if (!PHONE_DIGITS_RE.test(digits)) {
    return null;
  }

  return `${digits}@s.whatsapp.net`;
}

function safeErrorSummary(err: unknown): { name: string; message: string } | undefined {
  if (err instanceof Error) {
    return { name: err.name, message: err.message };
  }
  return undefined;
}

async function whatsappPlugin(
  app: FastifyInstance,
  options: WhatsappPluginOptions = {},
): Promise<void> {
  const sessionDir = options.sessionDir ?? (process.env.WA_SESSION_DIR || '/data/wa-session');
  const autoConnect = options.autoConnect ?? true;
  const initialReconnectDelayMs =
    options.initialReconnectDelayMs ?? DEFAULT_INITIAL_RECONNECT_DELAY_MS;
  const maxReconnectDelayMs = options.maxReconnectDelayMs ?? DEFAULT_MAX_RECONNECT_DELAY_MS;
  const maxReconnectAttempts = options.maxReconnectAttempts ?? DEFAULT_MAX_RECONNECT_ATTEMPTS;
  const random = options.random ?? Math.random;
  const deps: WhatsappDependencies = {
    ...defaultDependencies,
    ...options.deps,
  };

  fs.mkdirSync(sessionDir, { recursive: true });

  let socket: WaSocketLike | null = null;
  let status: WaStatus = 'disconnected';
  let qrDataUrl: string | null = null;
  let reconnectTimer: NodeJS.Timeout | null = null;
  let reconnectGeneration = 0;
  let connectingPromise: Promise<void> | null = null;
  let isLoggingOut = false;
  let isClosed = false;
  let reconnectFailures = 0;

  function clearReconnectTimer(): void {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  }

  function detachSocket(target: WaSocketLike | null): void {
    if (!target) return;
    target.ev.removeAllListeners('connection.update');
    target.ev.removeAllListeners('creds.update');
    target.ev.removeAllListeners('messages.upsert');
    target.end(undefined);
  }

  function scheduleReconnect(expectedGeneration: number): void {
    if (isClosed || isLoggingOut || expectedGeneration !== reconnectGeneration) {
      return;
    }
    if (reconnectTimer) {
      return;
    }
    if (reconnectFailures >= maxReconnectAttempts) {
      app.log.error('WhatsApp reconnect attempts exhausted');
      return;
    }
    const baseDelayMs = Math.min(
      maxReconnectDelayMs,
      initialReconnectDelayMs * 2 ** reconnectFailures,
    );
    const delayMs = Math.max(1, Math.round(baseDelayMs * (0.8 + random() * 0.4)));
    reconnectFailures += 1;
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      if (isClosed || isLoggingOut || expectedGeneration !== reconnectGeneration) {
        return;
      }
      void connect();
    }, delayMs);
    reconnectTimer.unref?.();
  }

  function connect(): Promise<void> {
    if (isClosed || isLoggingOut || socket) {
      return Promise.resolve();
    }
    if (connectingPromise) {
      return connectingPromise;
    }

    clearReconnectTimer();
    const generation = ++reconnectGeneration;

    const runAttempt = async (): Promise<void> => {
      try {
        fs.mkdirSync(sessionDir, { recursive: true });
        const { state, saveCreds } = await deps.useMultiFileAuthState(sessionDir);
        if (generation !== reconnectGeneration || isClosed || isLoggingOut) return;

        const { version } = await deps.fetchLatestBaileysVersion();
        if (generation !== reconnectGeneration || isClosed || isLoggingOut) return;

        const nextSocket = deps.makeWASocket({
          version,
          auth: state,
          printQRInTerminal: false,
        });
        if (generation !== reconnectGeneration || isClosed || isLoggingOut) {
          detachSocket(nextSocket);
          return;
        }

        socket = nextSocket;
        nextSocket.ev.on('creds.update', saveCreds);
        nextSocket.ev.on('messages.upsert', (rawUpsert: unknown) => {
          if (generation !== reconnectGeneration || isClosed || socket !== nextSocket) {
            return;
          }
          const upsert = rawUpsert as {
            messages?: Array<{
              key?: { remoteJid?: string; fromMe?: boolean };
              message?: {
                conversation?: string;
                extendedTextMessage?: { text?: string };
              };
            }>;
          };
          for (const msg of upsert.messages || []) {
            const remoteJid = msg.key?.remoteJid;
            if (!remoteJid || msg.key?.fromMe) continue;
            const text = (
              msg.message?.conversation ||
              msg.message?.extendedTextMessage?.text ||
              ''
            ).trim();
            const match = text.match(/^(?:\/sidra|!sidra)\s+(.+)$/i);
            if (!match || !deps.querySidra) continue;
            const sidraQuery = match[1].trim();
            if (!sidraQuery) continue;
            void deps
              .querySidra(sidraQuery, `wa:${remoteJid}`)
              .then((answer) => {
                if (socket === nextSocket && !isClosed) {
                  return nextSocket.sendMessage(remoteJid, {
                    text: answer.slice(0, MAX_MESSAGE_LENGTH),
                  });
                }
                return undefined;
              })
              .catch((err: unknown) => {
                app.log.error({ err: safeErrorSummary(err) }, 'Sidra WhatsApp query failed');
              });
          }
        });
        nextSocket.ev.on('connection.update', (raw: unknown) => {
          if (generation !== reconnectGeneration || isClosed || socket !== nextSocket) {
            return;
          }
          const update = raw as BaileysConnectionUpdate;
          const { connection, lastDisconnect, qr } = update;
          if (qr) {
            const qrGeneration = generation;
            deps
              .qrToDataUrl(qr)
              .then((dataUrl: string) => {
                if (
                  qrGeneration === reconnectGeneration &&
                  !isClosed &&
                  !isLoggingOut &&
                  status !== 'connected'
                ) {
                  qrDataUrl = dataUrl;
                }
              })
              .catch((err: unknown) => {
                app.log.error({ err: safeErrorSummary(err) }, 'Failed to render WhatsApp QR');
              });
          }
          if (connection === 'connecting') {
            status = 'connecting';
          }
          if (connection === 'open') {
            status = 'connected';
            qrDataUrl = null;
            reconnectFailures = 0;
            clearReconnectTimer();
            app.log.info('WhatsApp connected');
          }
          if (connection === 'close') {
            const err = lastDisconnect?.error;
            const code =
              err && typeof err === 'object' && 'output' in err
                ? err.output?.statusCode
                : undefined;
            detachSocket(nextSocket);
            socket = null;
            status = 'disconnected';
            qrDataUrl = null;
            if (code === DisconnectReason.loggedOut) {
              clearReconnectTimer();
              reconnectFailures = 0;
              app.log.warn('WhatsApp logged out; re-pair via /wa/qr after restart');
              return;
            }
            if (generation === reconnectGeneration && !isClosed && !isLoggingOut) {
              app.log.warn({ code }, 'WhatsApp disconnected, reconnecting');
              scheduleReconnect(generation);
            }
          }
        });
      } catch (err) {
        status = 'disconnected';
        qrDataUrl = null;
        app.log.error({ err: safeErrorSummary(err) }, 'Failed to initialize WhatsApp connection');
        if (generation === reconnectGeneration && !isClosed && !isLoggingOut) {
          scheduleReconnect(generation);
        }
      }
    };

    const attempt = runAttempt().finally(() => {
      if (connectingPromise === attempt) {
        connectingPromise = null;
      }
    });
    connectingPromise = attempt;
    return attempt;
  }

  app.decorate('wa', {
    get status(): WaStatus {
      return status;
    },
    connect,
  });

  app.get('/wa/status', async () => ({
    status,
    pairing_required: status !== 'connected',
    qr_available: status !== 'connected' && Boolean(qrDataUrl),
  }));

  app.get('/wa/qr', async (_req: FastifyRequest, reply: FastifyReply) => {
    if (status === 'connected' || !qrDataUrl) {
      return reply.code(404).send({ error: 'no pending qr' });
    }
    return { qr: qrDataUrl };
  });

  const sendBodySchema = {
    type: 'object',
    additionalProperties: false,
    required: ['to', 'message'],
    properties: {
      to: { type: 'string', minLength: 1, maxLength: 64 },
      message: { type: 'string', minLength: 1, maxLength: MAX_MESSAGE_LENGTH },
    },
  } as const;

  app.post(
    '/wa/send',
    { schema: { body: sendBodySchema } },
    async (req: FastifyRequest<{ Body: SendBody }>, reply: FastifyReply) => {
      const { to, message } = req.body;
      const jid = normalizeWhatsAppRecipient(to);
      if (!jid) {
        return reply.code(400).send({ error: 'to must be a valid phone number or WhatsApp JID' });
      }
      const trimmedMessage = message.trim();
      if (trimmedMessage.length === 0 || trimmedMessage.length > MAX_MESSAGE_LENGTH) {
        return reply.code(400).send({ error: 'message must be a non-empty string up to 4096 characters' });
      }
      if (status !== 'connected' || !socket) {
        return reply.code(503).send({ error: 'whatsapp not connected' });
      }
      try {
        await socket.sendMessage(jid, { text: trimmedMessage });
      } catch (err) {
        app.log.error({ err: safeErrorSummary(err) }, 'Failed to send WhatsApp message');
        return reply.code(503).send({ error: 'failed to send WhatsApp message' });
      }
      return { sent: true, to: jid };
    },
  );

  const logoutBodySchema = {
    anyOf: [
      { type: 'null' },
      { type: 'object', additionalProperties: false, maxProperties: 0 },
    ],
  } as const;

  app.post(
    '/wa/logout',
    {
      preValidation: async (request) => {
        if (request.body === undefined || request.body === '') {
          request.body = null;
        }
      },
      schema: { body: logoutBodySchema },
    },
    async () => {
      isLoggingOut = true;
      reconnectGeneration += 1;
      clearReconnectTimer();
      reconnectFailures = 0;
      const activeSocket = socket;
      socket = null;
      try {
        if (activeSocket) {
          await activeSocket.logout();
        }
      } catch (err) {
        app.log.warn({ err: safeErrorSummary(err) }, 'WhatsApp logout failed');
      } finally {
        detachSocket(activeSocket);
        qrDataUrl = null;
        status = 'disconnected';
        fs.rmSync(sessionDir, { recursive: true, force: true });
        isLoggingOut = false;
      }
      return { logged_out: true };
    },
  );

  app.addHook('onReady', async () => {
    if (autoConnect && !isClosed) {
      void connect();
    }
  });

  app.addHook('onClose', async () => {
    isClosed = true;
    reconnectGeneration += 1;
    clearReconnectTimer();
    detachSocket(socket);
    socket = null;
    qrDataUrl = null;
    status = 'disconnected';
    reconnectFailures = 0;
  });
}

export default fastifyPlugin(whatsappPlugin);
