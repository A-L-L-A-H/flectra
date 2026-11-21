import Fastify, { type FastifyInstance } from 'fastify';
import authHook from './auth.js';
import whatsapp, { type WaStatus, type WhatsappPluginOptions } from './plugins/whatsapp.js';

declare module 'fastify' {
  interface FastifyInstance {
    wa: {
      readonly status: WaStatus;
      connect(): Promise<void>;
    };
  }
}

export interface BuildAppOptions {
  logger?: boolean;
  bodyLimit?: number;
  token?: string;
  whatsapp?: WhatsappPluginOptions;
}

export async function buildApp(options: BuildAppOptions = {}): Promise<FastifyInstance> {
  const app = Fastify({
    logger: options.logger ?? true,
    bodyLimit: options.bodyLimit ?? 65536,
    ajv: {
      customOptions: {
        removeAdditional: false,
      },
    },
  });

  await app.register(authHook, { token: options.token });

  app.get('/health', async () => ({ ok: true, service: 'moonwitness-orchestrator' }));
  app.get('/status', async () => ({
    ok: true,
    uptime_s: Math.round(process.uptime()),
    wa: app.wa.status,
  }));

  await app.register(whatsapp, options.whatsapp);
  return app;
}
