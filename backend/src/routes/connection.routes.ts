import { FastifyInstance } from 'fastify';
import { ConnectionController } from '../controllers/connection.controller';

export async function connectionRoutes(fastify: FastifyInstance) {
  fastify.post('/connections', ConnectionController.create);
  fastify.get('/connections', ConnectionController.list);
  fastify.post('/connections/test', ConnectionController.test);
  fastify.get('/connections/:id/metadata', ConnectionController.getMetadata);
}
