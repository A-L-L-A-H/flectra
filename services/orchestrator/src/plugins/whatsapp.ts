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
import path from 'node:path';
import type { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';

type WaStatus = 'disconnected' | 'connecting' | 'connected';
type WaSocket = ReturnType<typeof makeWASocket>;

interface BaileysDisconnectInfo { error?: { output?: { statusCode?: number } } | Error; }interface BaileysConnectionUpdate {
  connection?: string;
  lastDisconnect?: { error?: BaileysDisconnectInfo };
  qr?: string;
}

async function whatsappPlugin(app: FastifyInstance): Promise<void> {
  const sessionDir = process.env.WA_SESSION_DIR || '/data/wa-session';
  fs.mkdirSync(sessionDir, { recursive: true });

  let socket: WaSocket | null = null;
  let status: WaStatus = 'disconnected';
  let qrDataUrl: string | null = null;

  async function connect(): Promise<void> {
    const { state, saveCreds } = await useMultiFileAuthState(sessionDir);
    const { version } = await fetchLatestBaileysVersion();
    socket = makeWASocket({ version, auth: state, printQRInTerminal: false });

    socket.ev.on('creds.update', saveCreds);

    socket.ev.on('connection.update', (raw: unknown) => {
      const update = raw as BaileysConnectionUpdate;
      const { connection, lastDisconnect, qr } = update;
      if (qr) {
        QRCode.toDataURL(qr).then((dataUrl: string) => { qrDataUrl = dataUrl; });
      }
      if (connection === 'connecting') status = 'connecting';
      if (connection === 'open') {
        status = 'connected';
        qrDataUrl = null;
        app.log.info('WhatsApp connected');
      }
      if (connection === 'close') {
        const err = lastDisconnect?.error;
        const code = err && 'output' in err ? (err.output as { statusCode?: number })?.statusCode : undefined;
        status = 'disconnected';
        if (code !== DisconnectReason.loggedOut) {
          app.log.warn({ code }, 'WhatsApp disconnected, reconnecting');
          void connect();
        } else {
          app.log.warn('WhatsApp logged out; re-pair via /wa/qr after restart');
        }
      }
    });
  }

  app.decorate('wa', {
    get status(): WaStatus { return status; },
  });

  app.get('/wa/status', async () => ({
    status,
    pairing_required: status !== 'connected' && !qrDataUrl,
  }));

  app.get('/wa/qr', async (_req: FastifyRequest, reply: FastifyReply) => {
    if (!qrDataUrl) return reply.code(404).send({ error: 'no pending qr' });
    return { qr: qrDataUrl };
  });

  interface SendBody { to?: string; message?: string; }

  app.post('/wa/send', async (req: FastifyRequest<{ Body?: SendBody }>, reply: FastifyReply) => {
    const { to, message } = req.body ?? {};
    if (!to || !message) return reply.code(400).send({ error: 'to and message are required' });
    if (status !== 'connected' || !socket) {
      return reply.code(503).send({ error: 'whatsapp not connected' });
    }
    const jid = to.includes('@') ? to : `${to.replace(/[^0-9]/g, '')}@s.whatsapp.net`;
    await socket.sendMessage(jid, { text: message });
    return { sent: true, to: jid };
  });

  app.post('/wa/logout', async () => {
    if (socket) await socket.logout();
    fs.rmSync(sessionDir, { recursive: true, force: true });
    status = 'disconnected';
    qrDataUrl = null;
    return { logged_out: true };
  });

  await connect();
}

export default fastifyPlugin(whatsappPlugin);
