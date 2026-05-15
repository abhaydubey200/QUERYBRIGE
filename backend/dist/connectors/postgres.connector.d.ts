import { BaseConnector, TestConnectionResult, SchemaDiscoveryResult } from './base.connector';
export declare class PostgresConnector extends BaseConnector {
    private pool;
    private getPool;
    test(): Promise<TestConnectionResult>;
    discoverSchema(): Promise<SchemaDiscoveryResult>;
    executeQuery(sql: string): Promise<any[]>;
    disconnect(): Promise<void>;
}
