// Shared-secret auth hook for every route.
import { timingSafeEqual, createHash } from 'node:crypto';
import fastifyPlugin from 'fastify-plugin';
import type { FastifyInstance, onRequestAsyncHookHandler } from 'fastify';

const AUTH_HEADER = 'x-orchestrator-token';

export interface AuthPluginOptions {
  token?: string;
}

async function authHook(app: FastifyInstance, options: AuthPluginOptions = {}): Promise<void> {
  const token = options.token ?? process.env.ORCHESTRATOR_TOKEN;
  if (!token) {
    app.log.error('ORCHESTRATOR_TOKEN is not set; refusing to start');
    throw new Error('ORCHESTRATOR_TOKEN is required');
  }

  const expectedTokenDigest = createHash('sha256').update(token).digest();

  const guard: onRequestAsyncHookHandler = async (request, reply) => {
    if (request.routeOptions?.url === '/health') return;
    const providedToken = request.headers[AUTH_HEADER];
    if (typeof providedToken !== 'string' || !isTokenValid(providedToken, expectedTokenDigest)) {
      request.log.warn({ request_id: request.id, ip: request.ip }, 'Unauthorized orchestrator request');
      return reply.code(401).send({ error: 'unauthorized' });
    }
  };

  app.addHook('onRequest', guard);
}

function isTokenValid(providedToken: string, expectedTokenDigest: Buffer): boolean {
  const providedTokenDigest = createHash('sha256').update(providedToken).digest();
  return timingSafeEqual(providedTokenDigest, expectedTokenDigest);
}

export default fastifyPlugin(authHook);
