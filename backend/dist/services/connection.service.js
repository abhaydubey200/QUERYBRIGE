"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConnectionService = void 0;
const connection_repository_1 = require("../repositories/connection.repository");
const postgres_connector_1 = require("../connectors/postgres.connector");
const ai_service_1 = require("./ai.service");
class ConnectionService {
    repo = new connection_repository_1.ConnectionRepository();
    async createConnection(config) {
        return await this.repo.create(config);
    }
    async getAllConnections() {
        return await this.repo.findAll();
    }
    async testConnection(config) {
        const connector = this.getConnector(config);
        const result = await connector.test();
        return result;
    }
    async discoverSchema(id) {
        const config = await this.repo.getFullConfig(id);
        if (!config)
            throw new Error('Connection not found');
        const connector = this.getConnector(config);
        const schema = await connector.discoverSchema();
        // AI Analysis in background or requested
        const aiInsight = await ai_service_1.AIService.analyzeSchema(schema);
        return { ...schema, aiInsight };
    }
    getConnector(config) {
        switch (config.type) {
            case 'postgres':
                return new postgres_connector_1.PostgresConnector(config);
            // Add other connectors here (Snowflake, MySQL, etc.)
            default:
                throw new Error(`Unsupported connector type: ${config.type}`);
        }
    }
}
exports.ConnectionService = ConnectionService;
//# sourceMappingURL=connection.service.js.map