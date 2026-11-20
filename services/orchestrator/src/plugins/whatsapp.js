// WhatsApp plugin backed by Baileys (no headless browser needed).
// Pairing: call POST /wa/pair, scan the QR returned in `qr` (data URL)
// from the phone that owns the session; session persists in WA_SESSION_DIR.
import fastifyPlugin from 'fastify-plugin';
import makeWASocket, {
  useMultiFileAuthState,
  fetchLatestBaileysVersion,
  DisconnectReason,
} from '@whiskeysockets/baileys';
import QRCode from 'qrcode';
import fs from 'node:fs';

async function whatsappPlugin(app) {
  const sessionDir = process.env.WA_SESSION_DIR || '/data/wa-session';
  fs.mkdirSync(sessionDir, { recursive: true });

  let socket = null;
  let status = 'disconnected';
  let qrDataUrl = null;

  async function connect() {
    const { state, saveCreds } = await useMultiFileAuthState(sessionDir);
    const { version } = await fetchLatestBaileysVersion();
    socket = makeWASocket({ version, auth: state, printQRInTerminal: false });

    socket.ev.on('creds.update', saveCreds);

    socket.ev.on('connection.update', (update) => {
      const { connection, lastDisconnect, qr } = update;
      if (qr) {
        QRCode.toDataURL(qr).then((dataUrl) => { qrDataUrl = dataUrl; });
      }
      if (connection === 'connecting') status = 'connecting';
      if (connection === 'open') {
        status = 'connected';
        qrDataUrl = null;
        app.log.info('WhatsApp connected');
      }
      if (connection === 'close') {
        const code = lastDisconnect?.error?.output?.statusCode;
        status = 'disconnected';
        if (code !== DisconnectReason.loggedOut) {
          app.log.warn({ code }, 'WhatsApp disconnected, reconnecting');
          connect();
        } else {
          app.log.warn('WhatsApp logged out; call /wa/pair to re-link');
        }
      }
    });
  }

  app.decorate('wa', {
    get status() { return status; },
  });

  app.get('/wa/status', async () => ({ status, pairing_required: status !== 'connected' && !qrDataUrl }));

  app.get('/wa/qr', async (_req, reply) => {
    if (!qrDataUrl) return reply.code(404).send({ error: 'no pending qr' });
    return { qr: qrDataUrl };
  });

  app.post('/wa/send', async (req, reply) => {
    const { to, message } = req.body || {};
    if (!to || !message) return reply.code(400).send({ error: 'to and message are required' });
    if (status !== 'connected') return reply.code(503).send({ error: 'whatsapp not connected' });
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

  connect();
}

export default fastifyPlugin(whatsappPlugin);
