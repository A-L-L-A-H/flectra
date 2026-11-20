import Fastify from 'fastify';
import authHook from './auth.js';
import whatsapp from './plugins/whatsapp.js';

declare module 'fastify' {
  interface FastifyInstance {
    wa: { readonly status: string };
  }
}

const app = Fastify({ logger: true });

await app.register(authHook);

app.get('/health', async () => ({ ok: true, service: 'moonwitness-orchestrator' }));
app.get('/status', async () => ({
  ok: true,
  uptime_s: Math.round(process.uptime()),
  wa: app.wa ? app.wa.status : 'plugin-missing',
}));

await app.register(whatsapp);

const port = Number(process.env.PORT || 8090);
await app.listen({ host: '0.0.0.0', port });
