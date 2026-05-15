"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.PostgresConnector = void 0;
const pg_1 = require("pg");
const base_connector_1 = require("./base.connector");
const pino_1 = __importDefault(require("pino"));
const logger = (0, pino_1.default)({ level: 'info' });
class PostgresConnector extends base_connector_1.BaseConnector {
    pool = null;
    async getPool() {
        if (!this.pool) {
            const sslConfig = this.config.ssl ? {
                rejectUnauthorized: true, // Enterprise-grade security: enforced CA validation
                ca: this.config.caCertificate,
                key: this.config.clientKey,
                cert: this.config.clientCertificate,
            } : false;
            this.pool = new pg_1.Pool({
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
    async test() {
        let retries = 3;
        let delay = 1000;
        while (retries > 0) {
            try {
                const { latencyMs } = await this.measureLatency(async () => {
                    const pool = await this.getPool();
                    const client = await pool.connect();
                    await client.query('SELECT 1');
                    client.release();
                });
                return {
                    success: true,
                    latencyMs,
                    message: 'Successfully connected to PostgreSQL',
                };
            }
            catch (error) {
                retries--;
                if (retries === 0) {
                    logger.error({ error: error.message, config: { ...this.config, password: '****' } }, 'Postgres test failed after retries');
                    return {
                        success: false,
                        latencyMs: 0,
                        message: 'Failed to connect to PostgreSQL after multiple attempts',
                        error: error.message,
                    };
                }
                logger.warn({ error: error.message, retriesLeft: retries }, 'Retrying Postgres connection...');
                await new Promise(resolve => setTimeout(resolve, delay));
                delay *= 2; // Exponential backoff
            }
        }
        return { success: false, latencyMs: 0, message: 'Unknown error' };
    }
    async discoverSchema() {
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
        const tablesMap = {};
        tableRes.rows.forEach(r => {
            const key = `${r.table_schema}.${r.table_name}`;
            if (!tablesMap[key]) {
                tablesMap[key] = { schema: r.table_schema, name: r.table_name, columns: [] };
            }
            const column = {
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
    async executeQuery(sql) {
        const pool = await this.getPool();
        const res = await pool.query(sql);
        return res.rows;
    }
    async disconnect() {
        if (this.pool) {
            await this.pool.end();
            this.pool = null;
        }
    }
}
exports.PostgresConnector = PostgresConnector;
//# sourceMappingURL=postgres.connector.js.map