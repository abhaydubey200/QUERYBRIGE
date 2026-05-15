import { FastifyRequest, FastifyReply } from 'fastify';
import { ConnectionConfig } from '../connectors/base.connector';
export declare class ConnectionController {
    static create(req: FastifyRequest<{
        Body: ConnectionConfig;
    }>, reply: FastifyReply): Promise<never>;
    static list(req: FastifyRequest, reply: FastifyReply): Promise<never>;
    static test(req: FastifyRequest<{
        Body: ConnectionConfig;
    }>, reply: FastifyReply): Promise<never>;
    static getMetadata(req: FastifyRequest<{
        Params: {
            id: string;
        };
    }>, reply: FastifyReply): Promise<never>;
}
