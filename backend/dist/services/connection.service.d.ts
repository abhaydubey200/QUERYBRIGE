import { ConnectionConfig, TestConnectionResult } from '../connectors/base.connector';
export declare class ConnectionService {
    private repo;
    createConnection(config: ConnectionConfig): Promise<any>;
    getAllConnections(): Promise<any[]>;
    testConnection(config: ConnectionConfig): Promise<TestConnectionResult>;
    discoverSchema(id: string): Promise<{
        aiInsight: string;
        schemas: string[];
        tables: {
            schema: string;
            name: string;
            columns: import("../connectors/base.connector").ColumnMetadata[];
        }[];
    }>;
    private getConnector;
}
