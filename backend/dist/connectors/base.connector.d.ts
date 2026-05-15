export interface ConnectionConfig {
    id?: string;
    name: string;
    type: 'postgres' | 'mysql' | 'mongodb' | 'snowflake' | 'oracle' | 'sqlserver';
    host: string;
    port: number;
    username: string;
    password?: string;
    database?: string;
    schema?: string;
    warehouse?: string;
    ssl?: boolean;
    caCertificate?: string;
    clientKey?: string;
    clientCertificate?: string;
    timeout?: number;
    poolSize?: number;
}
export interface SchemaDiscoveryResult {
    schemas: string[];
    tables: {
        schema: string;
        name: string;
        columns: ColumnMetadata[];
    }[];
}
export interface ColumnMetadata {
    name: string;
    type: string;
    isNullable: boolean;
    isPrimaryKey: boolean;
    isForeignKey: boolean;
    references?: {
        table: string;
        column: string;
    };
}
export interface TestConnectionResult {
    success: boolean;
    latencyMs: number;
    message: string;
    error?: string;
    details?: any;
}
/**
 * Abstract Base Connector
 */
export declare abstract class BaseConnector {
    protected config: ConnectionConfig;
    constructor(config: ConnectionConfig);
    abstract test(): Promise<TestConnectionResult>;
    abstract discoverSchema(): Promise<SchemaDiscoveryResult>;
    abstract executeQuery(sql: string): Promise<any[]>;
    abstract disconnect(): Promise<void>;
    protected measureLatency<T>(fn: () => Promise<T>): Promise<{
        result: T;
        latencyMs: number;
    }>;
}
