import { ConnectionRepository } from '../repositories/connection.repository';
import { PostgresConnector } from '../connectors/postgres.connector';
import { ConnectionConfig, TestConnectionResult } from '../connectors/base.connector';
import { AIService } from './ai.service';

export class ConnectionService {
  private repo = new ConnectionRepository();

  async createConnection(config: ConnectionConfig) {
    const normalized = this.normalizeConfig(config);
    return await this.repo.create(normalized);
  }

  async getAllConnections() {
    return await this.repo.findAll();
  }

  async testConnection(config: ConnectionConfig): Promise<TestConnectionResult> {
    const normalized = this.normalizeConfig(config);
    const connector = this.getConnector(normalized);
    const result = await connector.test();
    // Ensure we release the pool after testing
    await connector.disconnect();
    return result;
  }

  private normalizeConfig(config: any): ConnectionConfig {
    const advanced = { ...(config.advanced_settings || {}) };
    
    // Merge top-level keys into advanced_settings for parity with Python backend
    const keysToMerge = ['ssl_mode', 'schema_name', 'warehouse', 'role', 'auth_type', 'service_name', 'sid', 'authenticator', 'metadata_limit', 'charset'];
    keysToMerge.forEach(key => {
      if (config[key] !== undefined && config[key] !== '') {
        advanced[key] = config[key];
      }
    });

    return {
      ...config,
      type: config.db_type || config.type,
      schema: config.schema_name || config.schema,
      ssl: config.ssl || (config.ssl_mode && config.ssl_mode !== 'disable'),
      caCertificate: advanced.ssl_ca || config.ssl_ca || config.caCertificate,
      timeout: config.timeout || 30000,
      poolSize: config.poolSize || 10,
      advanced_settings: advanced
    };
  }

  async discoverSchema(id: string) {
    const config = await this.repo.getFullConfig(id);
    if (!config) throw new Error('Connection not found');
    
    const connector = this.getConnector(config);
    const schema = await connector.discoverSchema();
    
    // AI Analysis in background or requested
    const aiInsight = await AIService.analyzeSchema(schema);
    
    return { ...schema, aiInsight };
  }

  private getConnector(config: ConnectionConfig) {
    const type = config.db_type || config.type;
    
    switch (type) {
      case 'postgres':
        return new PostgresConnector(config);
      case 'mysql':
        // return new MySQLConnector(config);
        throw new Error('MySQL connector implementation pending stabilization');
      case 'snowflake':
        // return new SnowflakeConnector(config);
        throw new Error('Snowflake connector implementation pending stabilization');
      case 'mssql':
        // return new MSSQLConnector(config);
        throw new Error('MSSQL connector implementation pending stabilization');
      case 'oracle':
        // return new OracleConnector(config);
        throw new Error('Oracle connector implementation pending stabilization');
      default:
        throw new Error(`Unsupported connector type: ${type}`);
    }
  }
}
