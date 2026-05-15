"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MonitoringService = void 0;
const connection_repository_1 = require("../repositories/connection.repository");
const postgres_connector_1 = require("../connectors/postgres.connector");
class MonitoringService {
    static repo = new connection_repository_1.ConnectionRepository();
    static async startHealthMonitoring(fastify) {
        // Basic polling for health checks every 30 seconds
        setInterval(async () => {
            const connections = await this.repo.findAll();
            for (const conn of connections) {
                try {
                    const fullConfig = await this.repo.getFullConfig(conn.id);
                    if (!fullConfig)
                        continue;
                    const connector = new postgres_connector_1.PostgresConnector(fullConfig);
                    const result = await connector.test();
                    await this.repo.updateHealth(conn.id, result.success ? 'online' : 'offline', result.latencyMs);
                    // Broadcast to all websocket clients
                    fastify.websocketServer.clients.forEach((client) => {
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
                }
                catch (error) {
                    console.error(`Health check failed for ${conn.name}:`, error);
                }
            }
        }, 30000);
    }
}
exports.MonitoringService = MonitoringService;
//# sourceMappingURL=monitoring.service.js.map