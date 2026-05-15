import { FastifyRequest, FastifyReply } from 'fastify';
import { ConnectionService } from '../services/connection.service';
import { ConnectionConfig } from '../connectors/base.connector';

const service = new ConnectionService();

export class ConnectionController {
  static async create(req: FastifyRequest<{ Body: ConnectionConfig }>, reply: FastifyReply) {
    try {
      const connection = await service.createConnection(req.body);
      return reply.status(201).send(connection);
    } catch (error: any) {
      return reply.status(500).send({ error: error.message });
    }
  }

  static async list(req: FastifyRequest, reply: FastifyReply) {
    const connections = await service.getAllConnections();
    return reply.send(connections);
  }

  static async test(req: FastifyRequest<{ Body: ConnectionConfig }>, reply: FastifyReply) {
    const result = await service.testConnection(req.body);
    return reply.send(result);
  }

  static async getMetadata(req: FastifyRequest<{ Params: { id: string } }>, reply: FastifyReply) {
    try {
      const metadata = await service.discoverSchema(req.params.id);
      return reply.send(metadata);
    } catch (error: any) {
      return reply.status(404).send({ error: error.message });
    }
  }
}
