export interface ConnectionConfig {
  id?: string;
  name: string;
  type?: 'postgres' | 'mysql' | 'mongodb' | 'snowflake' | 'oracle' | 'sqlserver' | 'mssql' | 'clickhouse';
  db_type?: 'postgres' | 'mysql' | 'mongodb' | 'snowflake' | 'oracle' | 'sqlserver' | 'mssql' | 'clickhouse';
  host: string;
  port: number;
  username: string;
  password?: string;
  database?: string;
  schema?: string;
  schema_name?: string; // Frontend compatibility
  warehouse?: string; 
  role?: string;
  ssl?: boolean;
  ssl_mode?: string;
  caCertificate?: string;
  ssl_ca?: string; // Frontend compatibility
  clientKey?: string;
  clientCertificate?: string;
  timeout?: number;
  poolSize?: number;
  metadata_limit?: number;
  advanced_settings?: Record<string, any>;
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
  latency_ms: number;
  message: string;
  error?: string;
  version?: string;
  diagnostics?: Record<string, any>;
}

/**
 * Abstract Base Connector
 */
export abstract class BaseConnector {
  protected config: ConnectionConfig;

  constructor(config: ConnectionConfig) {
    this.config = config;
  }

  abstract test(): Promise<TestConnectionResult>;
  abstract discoverSchema(): Promise<SchemaDiscoveryResult>;
  abstract executeQuery(sql: string): Promise<any[]>;
  abstract disconnect(): Promise<void>;

  protected async measureLatency<T>(fn: () => Promise<T>): Promise<{ result: T; latency_ms: number }> {
    const start = Date.now();
    const result = await fn();
    const end = Date.now();
    return { result, latency_ms: end - start };
  }
}
