"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.connectionRoutes = connectionRoutes;
const connection_controller_1 = require("../controllers/connection.controller");
async function connectionRoutes(fastify) {
    fastify.post('/connections', connection_controller_1.ConnectionController.create);
    fastify.get('/connections', connection_controller_1.ConnectionController.list);
    fastify.post('/connections/test', connection_controller_1.ConnectionController.test);
    fastify.get('/connections/:id/metadata', connection_controller_1.ConnectionController.getMetadata);
}
//# sourceMappingURL=connection.routes.js.map