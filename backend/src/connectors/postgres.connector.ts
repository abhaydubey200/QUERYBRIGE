import { Pool } from 'pg';
import { BaseConnector, ConnectionConfig, TestConnectionResult, SchemaDiscoveryResult, ColumnMetadata } from './base.connector';
import pino from 'pino';

const logger = pino({ level: 'info' });

export class PostgresConnector extends BaseConnector {
  private pool: Pool | null = null;

  private async getPool(): Promise<Pool> {
    if (!this.pool) {
      let sslConfig: any = false;

      if (this.config.ssl_mode && this.config.ssl_mode !== 'disable') {
        sslConfig = {
          rejectUnauthorized: this.config.ssl_mode === 'verify-full' || this.config.ssl_mode === 'verify-ca',
          ca: this.config.caCertificate || this.config.ssl_ca,
          key: this.config.clientKey,
          cert: this.config.clientCertificate,
        };

        // If mode is 'require' but no CA, we still want SSL but won't verify
        if (this.config.ssl_mode === 'require' && !sslConfig.ca) {
          sslConfig.rejectUnauthorized = false;
        }
      } else if (this.config.ssl) {
        sslConfig = {
          rejectUnauthorized: true,
          ca: this.config.caCertificate,
        };
      }

      this.pool = new Pool({
        host: this.config.host,
        port: this.config.port,
        user: this.config.username,
        password: this.config.password,
        database: this.config.database,
        ssl: sslConfig,
        connectionTimeoutMillis: this.config.timeout || 5000,
        idleTimeoutMillis: 30000,
        max: this.config.poolSize || 20,
        application_name: 'QueryBridge_Enterprise',
      });

      this.pool.on('error', (err) => {
        logger.error({ err }, 'Unexpected error on idle client');
      });
    }
    return this.pool;
  }

  async test(): Promise<TestConnectionResult> {
    let retries = 3;
    let delay = 1000;

    while (retries > 0) {
      try {
        const { result: version, latency_ms } = await this.measureLatency(async () => {
          const pool = await this.getPool();
          const client = await pool.connect();
          try {
            const versionRes = await client.query('SELECT version()');
            return versionRes.rows[0].version;
          } finally {
            client.release();
          }
        });

        return {
          success: true,
          latency_ms,
          message: 'Successfully connected to PostgreSQL',
          version: version,
          diagnostics: {
            pool_size: this.config.poolSize || 20,
            ssl_enabled: !!this.config.ssl,
            database: this.config.database,
            driver: 'node-postgres',
          }
        };
      } catch (error: any) {
        retries--;
        if (retries === 0) {
          logger.error({ error: error.message, config: { ...this.config, password: '****' } }, 'Postgres test failed after retries');
          let suggestion = '';
          if (error.message.includes('ECONNREFUSED') && this.config.host === 'localhost' && this.config.port === 5432) {
            suggestion = 'Postgres might be running on port 5444 in your Docker setup. Try changing the port.';
          }

          return {
            success: false,
            latency_ms: 0,
            message: suggestion || 'Failed to connect to PostgreSQL after multiple attempts',
            error: error.message,
            diagnostics: {
              error_code: error.code,
              detail: error.detail,
              status: 'disconnected',
              recommendation: suggestion || 'Check host, port, and credentials.'
            }
          };
        }
        logger.warn({ error: error.message, retriesLeft: retries }, 'Retrying Postgres connection...');
        await new Promise(resolve => setTimeout(resolve, delay));
        delay *= 2; // Exponential backoff
      }
    }
    return { success: false, latency_ms: 0, message: 'Unknown error' };
  }

  async discoverSchema(): Promise<SchemaDiscoveryResult> {
    const pool = await this.getPool();
    
    // 1. Get Schemas
    const schemaRes = await pool.query(`
      SELECT schema_name 
      FROM information_schema.schemata 
      WHERE schema_name NOT IN ('information_schema', 'pg_catalog')
    `);
    const schemas = schemaRes.rows.map(r => r.schema_name);

    // 2. Get Tables and Columns
    const tableRes = await pool.query(`
      SELECT 
        table_schema, 
        table_name, 
        column_name, 
        data_type, 
        is_nullable,
        column_default
      FROM information_schema.columns
      WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
      ORDER BY table_schema, table_name, ordinal_position
    `);

    // 3. Get PKs
    const pkRes = await pool.query(`
      SELECT 
        kcu.table_schema,
        kcu.table_name, 
        kcu.column_name 
      FROM information_schema.table_constraints tc 
      JOIN information_schema.key_column_usage kcu 
        ON tc.constraint_name = kcu.constraint_name 
        AND tc.table_schema = kcu.table_schema
      WHERE tc.constraint_type = 'PRIMARY KEY'
    `);

    const pkMap = new Map();
    pkRes.rows.forEach(r => {
      pkMap.set(`${r.table_schema}.${r.table_name}.${r.column_name}`, true);
    });

    const tablesMap: any = {};
    tableRes.rows.forEach(r => {
      const key = `${r.table_schema}.${r.table_name}`;
      if (!tablesMap[key]) {
        tablesMap[key] = { schema: r.table_schema, name: r.table_name, columns: [] };
      }
      
      const column: ColumnMetadata = {
        name: r.column_name,
        type: r.data_type,
        isNullable: r.is_nullable === 'YES',
        isPrimaryKey: pkMap.has(`${r.table_schema}.${r.table_name}.${r.column_name}`),
        isForeignKey: false, // Simplified for now
      };
      
      tablesMap[key].columns.push(column);
    });

    return {
      schemas,
      tables: Object.values(tablesMap),
    };
  }

  async executeQuery(sql: string): Promise<any[]> {
    const pool = await this.getPool();
    const res = await pool.query(sql);
    return res.rows;
  }

  async disconnect(): Promise<void> {
    if (this.pool) {
      await this.pool.end();
      this.pool = null;
    }
  }
}
