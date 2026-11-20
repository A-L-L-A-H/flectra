// Shared-secret auth hook for every route.
import type { FastifyInstance, onRequestAsyncHookHandler } from 'fastify';

const AUTH_HEADER = 'x-orchestrator-token';

export default async function authHook(app: FastifyInstance): Promise<void> {
  const token = process.env.ORCHESTRATOR_TOKEN;
  if (!token) {
    app.log.error('ORCHESTRATOR_TOKEN is not set; refusing to start');
    process.exit(1);
  }

  const guard: onRequestAsyncHookHandler = async (request, reply) => {
    if (request.url === '/health') return;
    if (request.headers[AUTH_HEADER] !== token) {
      return reply.code(401).send({ error: 'unauthorized' });
    }
  };

  app.addHook('onRequest', guard);
}
