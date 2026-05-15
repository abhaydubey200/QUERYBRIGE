import { FastifyInstance } from 'fastify';
export declare class MonitoringService {
    private static repo;
    static startHealthMonitoring(fastify: FastifyInstance): Promise<void>;
}
