import { buildApp } from './app.js';

const app = await buildApp();
await app.ready();

const port = Number(process.env.PORT || 8090);
await app.listen({ host: '0.0.0.0', port });

for (const signal of ['SIGTERM', 'SIGINT'] as const) {
  process.on(signal, async () => {
    await app.close();
    process.exit(0);
  });
}
