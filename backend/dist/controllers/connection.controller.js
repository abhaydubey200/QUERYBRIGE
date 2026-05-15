"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConnectionController = void 0;
const connection_service_1 = require("../services/connection.service");
const service = new connection_service_1.ConnectionService();
class ConnectionController {
    static async create(req, reply) {
        try {
            const connection = await service.createConnection(req.body);
            return reply.status(201).send(connection);
        }
        catch (error) {
            return reply.status(500).send({ error: error.message });
        }
    }
    static async list(req, reply) {
        const connections = await service.getAllConnections();
        return reply.send(connections);
    }
    static async test(req, reply) {
        const result = await service.testConnection(req.body);
        return reply.send(result);
    }
    static async getMetadata(req, reply) {
        try {
            const metadata = await service.discoverSchema(req.params.id);
            return reply.send(metadata);
        }
        catch (error) {
            return reply.status(404).send({ error: error.message });
        }
    }
}
exports.ConnectionController = ConnectionController;
//# sourceMappingURL=connection.controller.js.map