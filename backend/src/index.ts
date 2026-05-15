import Fastify from 'fastify';
import cors from '@fastify/cors';
import jwt from '@fastify/jwt';
import websocket from '@fastify/websocket';
import { connectionRoutes } from './routes/connection.routes';
import dotenv from 'dotenv';
import pino from 'pino';

dotenv.config();

const logger = pino({
  transport: {
    target: 'pino-pretty',
    options: { colorize: true }
  }
});

const fastify = Fastify({ 
  logger: logger as any,
  ignoreTrailingSlash: true
});

// Global Error Handler to prevent ERR_EMPTY_RESPONSE
fastify.setErrorHandler((error, request, reply) => {
  fastify.log.error(error);
  reply.status(500).send({ 
    success: false, 
    error: 'Internal Server Error', 
    message: error.message 
  });
});

async function bootstrap() {
  try {
    // Register Plugins
    await fastify.register(cors, { origin: '*' });
    await fastify.register(jwt, { secret: process.env.JWT_SECRET || 'querybridge-super-secret' });
    await fastify.register(websocket);

    // Register Routes
    await fastify.register(connectionRoutes, { prefix: '/api/v1' });

    // Health Check
    fastify.get('/health', async () => ({ status: 'UP', timestamp: new Date().toISOString() }));

    const port = Number(process.env.PORT) || 8000;
    await fastify.listen({ port, host: '0.0.0.0' });
    
    console.log(`🚀 QueryBridge Backend running at http://localhost:${port}`);
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
}

bootstrap();
