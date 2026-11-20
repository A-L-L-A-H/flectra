// Shared-secret auth hook for every route.
const AUTH_HEADER = 'x-orchestrator-token';

export default async function authHook(app) {
  const token = process.env.ORCHESTRATOR_TOKEN;
  if (!token) {
    app.log.error('ORCHESTRATOR_TOKEN is not set; refusing to start');
    process.exit(1);
  }

  app.addHook('onRequest', async (request, reply) => {
    if (request.url === '/health') return;
    if (request.headers[AUTH_HEADER] !== token) {
      return reply.code(401).send({ error: 'unauthorized' });
    }
  });
}
