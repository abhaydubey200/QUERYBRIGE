import { FastifyInstance } from 'fastify';
import { ConnectionRepository } from '../repositories/connection.repository';
import { PostgresConnector } from '../connectors/postgres.connector';

export class MonitoringService {
  private static repo = new ConnectionRepository();

  static async startHealthMonitoring(fastify: FastifyInstance) {
    // Basic polling for health checks every 30 seconds
    setInterval(async () => {
      const connections = await this.repo.findAll();
      
      for (const conn of connections) {
        try {
          const fullConfig = await this.repo.getFullConfig(conn.id);
          if (!fullConfig) continue;

          const connector = new PostgresConnector(fullConfig);
          const result = await connector.test();
          
          await this.repo.updateHealth(conn.id, result.success ? 'online' : 'offline', result.latencyMs);

          // Broadcast to all websocket clients
          fastify.websocketServer.clients.forEach((client: any) => {
            if (client.readyState === 1) {
              client.send(JSON.stringify({
                type: 'HEALTH_UPDATE',
                payload: {
                  id: conn.id,
                  status: result.success ? 'online' : 'offline',
                  latency: result.latencyMs
                }
              }));
            }
          });
        } catch (error: any) {
          console.error(`Health check failed for ${conn.name}:`, error);
        }
      }
    }, 30000);
  }
}
