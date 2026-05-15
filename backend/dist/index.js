"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const fastify_1 = __importDefault(require("fastify"));
const cors_1 = __importDefault(require("@fastify/cors"));
const jwt_1 = __importDefault(require("@fastify/jwt"));
const websocket_1 = __importDefault(require("@fastify/websocket"));
const connection_routes_1 = require("./routes/connection.routes");
const dotenv_1 = __importDefault(require("dotenv"));
const pino_1 = __importDefault(require("pino"));
dotenv_1.default.config();
const logger = (0, pino_1.default)({
    transport: {
        target: 'pino-pretty',
        options: { colorize: true }
    }
});
const fastify = (0, fastify_1.default)({ logger: logger });
async function bootstrap() {
    try {
        // Register Plugins
        await fastify.register(cors_1.default, { origin: '*' });
        await fastify.register(jwt_1.default, { secret: process.env.JWT_SECRET || 'querybridge-super-secret' });
        await fastify.register(websocket_1.default);
        // Register Routes
        await fastify.register(connection_routes_1.connectionRoutes, { prefix: '/api/v1' });
        // Health Check
        fastify.get('/health', async () => ({ status: 'UP', timestamp: new Date().toISOString() }));
        const port = Number(process.env.PORT) || 4000;
        await fastify.listen({ port, host: '0.0.0.0' });
        console.log(`🚀 QueryBridge Backend running at http://localhost:${port}`);
    }
    catch (err) {
        fastify.log.error(err);
        process.exit(1);
    }
}
bootstrap();
//# sourceMappingURL=index.js.map