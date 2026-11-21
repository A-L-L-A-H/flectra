import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { DisconnectReason } from '@whiskeysockets/baileys';
import { buildApp } from '../src/app.js';
import type {
  WaSocketLike,
  WhatsappDependencies,
  WhatsappPluginOptions,
} from '../src/plugins/whatsapp.js';

const TEST_TOKEN = 'test-orchestrator-secret-token';
const AUTH_HEADERS = { 'x-orchestrator-token': TEST_TOKEN };

interface FakeSocketRecord {
  socket: WaSocketLike;
  emitter: EventEmitter;
  sentMessages: Array<{ jid: string; text: string }>;
  logoutCalls: number;
  endCalls: number;
  removedListenerEvents: Array<string | undefined>;
}

function createFakeSocket(): FakeSocketRecord {
  const emitter = new EventEmitter();
  const record: FakeSocketRecord = {
    emitter,
    sentMessages: [],
    logoutCalls: 0,
    endCalls: 0,
    removedListenerEvents: [],
    socket: {
      ev: {
        on(event, listener) {
          emitter.on(event, listener);
        },
        removeAllListeners(event) {
          record.removedListenerEvents.push(event);
          emitter.removeAllListeners(event);
        },
      },
      async sendMessage(jid, content) {
        record.sentMessages.push({ jid, text: content.text });
        return { key: { id: 'fake-message-id' } };
      },
      async logout() {
        record.logoutCalls += 1;
      },
      end() {
        record.endCalls += 1;
      },
    },
  };
  return record;
}

async function withTestApp<T>(
  whatsappOptions: Omit<WhatsappPluginOptions, 'sessionDir'> = {},
  run: (ctx: {
    app: Awaited<ReturnType<typeof buildApp>>;
    sessionDir: string;
    sockets: FakeSocketRecord[];
    counts: {
      useAuthCalls: number;
      fetchVersionCalls: number;
      makeSocketCalls: number;
      qrCalls: number;
    };
  }) => Promise<T>,
): Promise<T> {
  const sessionDir = fs.mkdtempSync(path.join(os.tmpdir(), 'moonwitness-orch-test-'));
  const sockets: FakeSocketRecord[] = [];
  const counts = {
    useAuthCalls: 0,
    fetchVersionCalls: 0,
    makeSocketCalls: 0,
    qrCalls: 0,
  };

  const defaultFakeDeps: WhatsappDependencies = {
    useMultiFileAuthState: async () => {
      counts.useAuthCalls += 1;
      return { state: { creds: {} }, saveCreds: async () => {} };
    },
    fetchLatestBaileysVersion: async () => {
      counts.fetchVersionCalls += 1;
      return { version: [2, 3000, 1] };
    },
    makeWASocket: () => {
      counts.makeSocketCalls += 1;
      const created = createFakeSocket();
      sockets.push(created);
      return created.socket;
    },
    qrToDataUrl: async (rawQr) => {
      counts.qrCalls += 1;
      return `data:image/png;base64,${Buffer.from(rawQr).toString('base64')}`;
    },
  };

  const app = await buildApp({
    logger: false,
    token: TEST_TOKEN,
    whatsapp: {
      sessionDir,
      initialReconnectDelayMs: 25,
      maxReconnectDelayMs: 80,
      random: () => 0.5,
      ...whatsappOptions,
      deps: {
        ...defaultFakeDeps,
        ...whatsappOptions.deps,
      },
    },
  });

  try {
    return await run({ app, sessionDir, sockets, counts });
  } finally {
    await app.close();
    fs.rmSync(sessionDir, { recursive: true, force: true });
  }
}

describe('orchestrator HTTP auth and health', () => {
  it('serves GET /health and GET /health?foo=bar publicly without a token', async () => {
    await withTestApp({ autoConnect: false }, async ({ app }) => {
      const plainRes = await app.inject({ method: 'GET', url: '/health' });
      assert.equal(plainRes.statusCode, 200);
      assert.deepEqual(plainRes.json(), { ok: true, service: 'moonwitness-orchestrator' });

      const queryRes = await app.inject({ method: 'GET', url: '/health?foo=bar' });
      assert.equal(queryRes.statusCode, 200);
      assert.deepEqual(queryRes.json(), { ok: true, service: 'moonwitness-orchestrator' });
    });
  });

  it('protects GET /status against missing or invalid token and allows valid token', async () => {
    await withTestApp({ autoConnect: false }, async ({ app }) => {
      const missingRes = await app.inject({ method: 'GET', url: '/status' });
      assert.equal(missingRes.statusCode, 401);
      assert.deepEqual(missingRes.json(), { error: 'unauthorized' });

      const wrongRes = await app.inject({
        method: 'GET',
        url: '/status',
        headers: { 'x-orchestrator-token': 'wrong-token' },
      });
      assert.equal(wrongRes.statusCode, 401);

      const okRes = await app.inject({
        method: 'GET',
        url: '/status',
        headers: AUTH_HEADERS,
      });
      assert.equal(okRes.statusCode, 200);
      const payload = okRes.json();
      assert.equal(payload.ok, true);
      assert.equal(payload.wa, 'disconnected');
      assert.equal(typeof payload.uptime_s, 'number');
    });
  });
});

describe('WhatsApp status and QR pairing states', () => {
  it('reports disconnected (no QR), disconnected (with QR), and connected states accurately', async () => {
    await withTestApp({ autoConnect: false }, async ({ app, sockets }) => {
      await app.ready();
      await app.wa.connect();
      assert.equal(sockets.length, 1);

      // 1. Disconnected with no QR
      const noQrStatus = await app.inject({
        method: 'GET',
        url: '/wa/status',
        headers: AUTH_HEADERS,
      });
      assert.equal(noQrStatus.statusCode, 200);
      assert.deepEqual(noQrStatus.json(), {
        status: 'disconnected',
        pairing_required: true,
        qr_available: false,
      });

      const noQrRes = await app.inject({
        method: 'GET',
        url: '/wa/qr',
        headers: AUTH_HEADERS,
      });
      assert.equal(noQrRes.statusCode, 404);

      // 2. Disconnected with QR pending
      sockets[0].emitter.emit('connection.update', { qr: 'pairing-qr-payload' });
      await delay(10);

      const withQrStatus = await app.inject({
        method: 'GET',
        url: '/wa/status',
        headers: AUTH_HEADERS,
      });
      assert.equal(withQrStatus.statusCode, 200);
      assert.deepEqual(withQrStatus.json(), {
        status: 'disconnected',
        pairing_required: true,
        qr_available: true,
      });

      const withQrRes = await app.inject({
        method: 'GET',
        url: '/wa/qr',
        headers: AUTH_HEADERS,
      });
      assert.equal(withQrRes.statusCode, 200);
      assert.equal(
        withQrRes.json().qr,
        `data:image/png;base64,${Buffer.from('pairing-qr-payload').toString('base64')}`,
      );

      // 3. Connected
      sockets[0].emitter.emit('connection.update', { connection: 'connecting' });
      const connectingStatus = await app.inject({
        method: 'GET',
        url: '/wa/status',
        headers: AUTH_HEADERS,
      });
      assert.deepEqual(connectingStatus.json(), {
        status: 'connecting',
        pairing_required: true,
        qr_available: true,
      });

      sockets[0].emitter.emit('connection.update', { connection: 'open' });
      const connectedStatus = await app.inject({
        method: 'GET',
        url: '/wa/status',
        headers: AUTH_HEADERS,
      });
      assert.equal(connectedStatus.statusCode, 200);
      assert.deepEqual(connectedStatus.json(), {
        status: 'connected',
        pairing_required: false,
        qr_available: false,
      });

      const connectedQrRes = await app.inject({
        method: 'GET',
        url: '/wa/qr',
        headers: AUTH_HEADERS,
      });
      assert.equal(connectedQrRes.statusCode, 404);
    });
  });
});

describe('POST /wa/send validation and delivery', () => {
  it('validates recipients and messages, returns 503 when disconnected, and normalizes when connected', async () => {
    await withTestApp({ autoConnect: false }, async ({ app, sockets }) => {
      await app.ready();
      await app.wa.connect();

      // Disconnected returns 503 for valid input
      const disconnectedRes = await app.inject({
        method: 'POST',
        url: '/wa/send',
        headers: AUTH_HEADERS,
        payload: { to: '+62 812-3456-7890', message: 'Hello offline' },
      });
      assert.equal(disconnectedRes.statusCode, 503);

      // Invalid inputs return 400 even when disconnected
      const invalidCases = [
        { to: '6281234567890@g.us', message: 'group jid rejected' },
        { to: '6281234567890@evil.example', message: 'arbitrary domain rejected' },
        { to: '0123456789@s.whatsapp.net', message: 'leading zero jid rejected' },
        { to: '', message: 'empty phone' },
        { to: '1234567', message: 'too short phone' },
        { to: '1234567890123456', message: 'too long phone' },
        { to: '081234567890', message: 'leading zero phone' },
        { to: '62812abc3456', message: 'letters in phone' },
        { to: '+62 812-3456-7890', message: '   \t\n  ' },
        { to: '+62 812-3456-7890', message: 'x'.repeat(4097) },
        { to: '+62 812-3456-7890', message: 'hi', extra: 'not-allowed' },
      ];

      for (const payload of invalidCases) {
        const badRes = await app.inject({
          method: 'POST',
          url: '/wa/send',
          headers: AUTH_HEADERS,
          payload,
        });
        assert.equal(
          badRes.statusCode,
          400,
          `expected 400 for payload ${JSON.stringify(payload).slice(0, 80)}`,
        );
      }

      // Mark connected
      sockets[0].emitter.emit('connection.update', { connection: 'open' });

      // Formatted phone normalization
      const formattedRes = await app.inject({
        method: 'POST',
        url: '/wa/send',
        headers: AUTH_HEADERS,
        payload: { to: '+62 812-3456-7890', message: '  Hello formatted  ' },
      });
      assert.equal(formattedRes.statusCode, 200);
      assert.deepEqual(formattedRes.json(), {
        sent: true,
        to: '6281234567890@s.whatsapp.net',
      });

      // Explicit user JID
      const jidRes = await app.inject({
        method: 'POST',
        url: '/wa/send',
        headers: AUTH_HEADERS,
        payload: { to: '6281234567890@s.whatsapp.net', message: 'Hello JID' },
      });
      assert.equal(jidRes.statusCode, 200);
      assert.deepEqual(jidRes.json(), {
        sent: true,
        to: '6281234567890@s.whatsapp.net',
      });

      assert.deepEqual(sockets[0].sentMessages, [
        { jid: '6281234567890@s.whatsapp.net', text: 'Hello formatted' },
        { jid: '6281234567890@s.whatsapp.net', text: 'Hello JID' },
      ]);
    });
  });
});

describe('POST /wa/logout body validation', () => {
  it('accepts {}, null, and empty body, and rejects extra fields', async () => {
    await withTestApp({ autoConnect: false }, async ({ app }) => {
      const objRes = await app.inject({
        method: 'POST',
        url: '/wa/logout',
        headers: AUTH_HEADERS,
        payload: {},
      });
      assert.equal(objRes.statusCode, 200);
      assert.deepEqual(objRes.json(), { logged_out: true });

      const nullRes = await app.inject({
        method: 'POST',
        url: '/wa/logout',
        headers: { ...AUTH_HEADERS, 'content-type': 'application/json' },
        payload: 'null',
      });
      assert.equal(nullRes.statusCode, 200);
      assert.deepEqual(nullRes.json(), { logged_out: true });

      const emptyRes = await app.inject({
        method: 'POST',
        url: '/wa/logout',
        headers: AUTH_HEADERS,
      });
      assert.equal(emptyRes.statusCode, 200);
      assert.deepEqual(emptyRes.json(), { logged_out: true });

      const extraRes = await app.inject({
        method: 'POST',
        url: '/wa/logout',
        headers: AUTH_HEADERS,
        payload: { unexpected: true },
      });
      assert.equal(extraRes.statusCode, 400);
    });
  });
});

describe('WhatsApp non-blocking startup, single-flight, reconnect, and shutdown', () => {
  it('starts HTTP server and serves /health even when fetchLatestBaileysVersion throws', async () => {
    let fetchAttempts = 0;
    await withTestApp(
      {
        autoConnect: true,
        initialReconnectDelayMs: 500,
        deps: {
          fetchLatestBaileysVersion: async () => {
            fetchAttempts += 1;
            throw new Error('simulated offline DNS failure');
          },
        },
      },
      async ({ app }) => {
        const healthRes = await app.inject({ method: 'GET', url: '/health' });
        assert.equal(healthRes.statusCode, 200);
        assert.deepEqual(healthRes.json(), { ok: true, service: 'moonwitness-orchestrator' });

        const statusRes = await app.inject({
          method: 'GET',
          url: '/wa/status',
          headers: AUTH_HEADERS,
        });
        assert.equal(statusRes.statusCode, 200);
        assert.deepEqual(statusRes.json(), {
          status: 'disconnected',
          pairing_required: true,
          qr_available: false,
        });
        assert.ok(fetchAttempts >= 1);
      },
    );
  });

  it('does not block HTTP readiness when fetchLatestBaileysVersion hangs and aborts cleanly on close', async () => {
    let releaseStalledFetch!: () => void;
    const stalledFetch = new Promise<void>((resolve) => {
      releaseStalledFetch = resolve;
    });
    let makeSocketCalls = 0;

    const sessionDir = fs.mkdtempSync(path.join(os.tmpdir(), 'moonwitness-orch-hang-'));
    const app = await buildApp({
      logger: false,
      token: TEST_TOKEN,
      whatsapp: {
        sessionDir,
        autoConnect: true,
        deps: {
          useMultiFileAuthState: async () => ({
            state: { creds: {} },
            saveCreds: async () => {},
          }),
          fetchLatestBaileysVersion: async () => {
            await stalledFetch;
            return { version: [2, 3000, 1] };
          },
          makeWASocket: () => {
            makeSocketCalls += 1;
            return createFakeSocket().socket;
          },
          qrToDataUrl: async (rawQr) => `data:image/png;base64,${rawQr}`,
        },
      },
    });

    try {
      const healthRes = await app.inject({ method: 'GET', url: '/health' });
      assert.equal(healthRes.statusCode, 200);
      await app.close();
      releaseStalledFetch();
      await delay(20);
      assert.equal(makeSocketCalls, 0);
    } finally {
      fs.rmSync(sessionDir, { recursive: true, force: true });
    }
  });

  it('caps reconnect retries at maxReconnectAttempts without spinning', async () => {
    let attempts = 0;
    await withTestApp(
      {
        autoConnect: false,
        initialReconnectDelayMs: 10,
        maxReconnectDelayMs: 20,
        maxReconnectAttempts: 2,
        deps: {
          fetchLatestBaileysVersion: async () => {
            attempts += 1;
            throw new Error('offline');
          },
        },
      },
      async ({ app }) => {
        await app.ready();
        await app.wa.connect();
        await delay(120);
        // 1 initial attempt + 2 scheduled retries = 3 total attempts
        assert.equal(attempts, 3);
      },
    );
  });

  it('enforces single-flight connection guard across concurrent connect calls', async () => {
    let releaseVersionFetch!: () => void;
    const versionGate = new Promise<void>((resolve) => {
      releaseVersionFetch = resolve;
    });
    let fetchCalls = 0;

    await withTestApp(
      {
        autoConnect: false,
        deps: {
          fetchLatestBaileysVersion: async () => {
            fetchCalls += 1;
            await versionGate;
            return { version: [2, 3000, 1] };
          },
        },
      },
      async ({ app, sockets, counts }) => {
        await app.ready();
        const first = app.wa.connect();
        const second = app.wa.connect();
        const third = app.wa.connect();
        assert.equal(first, second);
        assert.equal(second, third);

        releaseVersionFetch();
        await Promise.all([first, second, third]);

        assert.equal(fetchCalls, 1);
        assert.equal(counts.makeSocketCalls, 1);
        assert.equal(sockets.length, 1);

        // Calling connect again while socket is active is a no-op
        await app.wa.connect();
        assert.equal(fetchCalls, 1);
        assert.equal(counts.makeSocketCalls, 1);
      },
    );
  });

  it('does not auto-reconnect after DisconnectReason.loggedOut', async () => {
    await withTestApp(
      {
        autoConnect: false,
        initialReconnectDelayMs: 20,
      },
      async ({ app, sockets, counts }) => {
        await app.ready();
        await app.wa.connect();
        assert.equal(counts.makeSocketCalls, 1);

        sockets[0].emitter.emit('connection.update', {
          connection: 'close',
          lastDisconnect: { error: { output: { statusCode: DisconnectReason.loggedOut } } },
        });

        await delay(80);
        assert.equal(counts.makeSocketCalls, 1);
        assert.equal(app.wa.status, 'disconnected');
      },
    );
  });

  it('cancels pending reconnect timers and closes active sockets on app.close()', async () => {
    const sessionDir = fs.mkdtempSync(path.join(os.tmpdir(), 'moonwitness-orch-close-'));
    const sockets: FakeSocketRecord[] = [];
    let fetchCalls = 0;

    const app = await buildApp({
      logger: false,
      token: TEST_TOKEN,
      whatsapp: {
        sessionDir,
        autoConnect: false,
        initialReconnectDelayMs: 40,
        random: () => 0.5,
        deps: {
          useMultiFileAuthState: async () => ({
            state: { creds: {} },
            saveCreds: async () => {},
          }),
          fetchLatestBaileysVersion: async () => {
            fetchCalls += 1;
            return { version: [2, 3000, 1] };
          },
          makeWASocket: () => {
            const created = createFakeSocket();
            sockets.push(created);
            return created.socket;
          },
          qrToDataUrl: async (rawQr) => `data:image/png;base64,${rawQr}`,
        },
      },
    });

    try {
      await app.ready();
      await app.wa.connect();
      assert.equal(sockets.length, 1);
      assert.equal(fetchCalls, 1);

      // Trigger transient disconnect -> schedules reconnect timer (~40ms)
      sockets[0].emitter.emit('connection.update', {
        connection: 'close',
        lastDisconnect: { error: { output: { statusCode: 500 } } },
      });

      // Immediately close app before timer fires
      await app.close();
      await delay(100);

      // Pending reconnect timer must not have fired
      assert.equal(fetchCalls, 1);
      assert.equal(sockets.length, 1);
      assert.ok(sockets[0].endCalls >= 1);
      assert.ok(sockets[0].removedListenerEvents.includes('connection.update'));
      assert.ok(sockets[0].removedListenerEvents.includes('creds.update'));
    } finally {
      fs.rmSync(sessionDir, { recursive: true, force: true });
    }

    // Also verify closing an app with an active connected socket cleans up listeners & ends socket
    const sessionDirActive = fs.mkdtempSync(path.join(os.tmpdir(), 'moonwitness-orch-active-'));
    const activeSockets: FakeSocketRecord[] = [];
    const activeApp = await buildApp({
      logger: false,
      token: TEST_TOKEN,
      whatsapp: {
        sessionDir: sessionDirActive,
        autoConnect: false,
        deps: {
          useMultiFileAuthState: async () => ({
            state: { creds: {} },
            saveCreds: async () => {},
          }),
          fetchLatestBaileysVersion: async () => ({ version: [2, 3000, 1] }),
          makeWASocket: () => {
            const created = createFakeSocket();
            activeSockets.push(created);
            return created.socket;
          },
          qrToDataUrl: async (rawQr) => `data:image/png;base64,${rawQr}`,
        },
      },
    });

    try {
      await activeApp.ready();
      await activeApp.wa.connect();
      activeSockets[0].emitter.emit('connection.update', { connection: 'open' });
      assert.equal(activeApp.wa.status, 'connected');

      await activeApp.close();
      assert.equal(activeSockets[0].endCalls, 1);
      assert.ok(activeSockets[0].removedListenerEvents.includes('connection.update'));
      assert.ok(activeSockets[0].removedListenerEvents.includes('creds.update'));
    } finally {
      fs.rmSync(sessionDirActive, { recursive: true, force: true });
    }
  });

  it('auto-replies to incoming /sidra <query> WhatsApp messages with verified Sidra answer', async () => {
    const sidraCalls: Array<{ query: string; sessionId: string }> = [];
    await withTestApp(
      {
        autoConnect: false,
        deps: {
          querySidra: async (query, sessionId) => {
            sidraCalls.push({ query, sessionId });
            return '[1] Quran 1:1 (Islam): "Dengan nama Allah Yang Maha Pengasih, Maha Penyayang."';
          },
        },
      },
      async ({ app, sockets }) => {
        await app.ready();
        await app.wa.connect();
        sockets[0].emitter.emit('connection.update', { connection: 'open' });

        sockets[0].emitter.emit('messages.upsert', {
          messages: [
            {
              key: { remoteJid: '6281234567890@s.whatsapp.net', fromMe: false },
              message: { conversation: '/sidra Maha Pengasih' },
            },
          ],
        });

        await delay(30);
        assert.deepEqual(sidraCalls, [
          { query: 'Maha Pengasih', sessionId: 'wa:6281234567890@s.whatsapp.net' },
        ]);
        assert.deepEqual(sockets[0].sentMessages, [
          {
            jid: '6281234567890@s.whatsapp.net',
            text: '[1] Quran 1:1 (Islam): "Dengan nama Allah Yang Maha Pengasih, Maha Penyayang."',
          },
        ]);
      },
    );
  });
});
