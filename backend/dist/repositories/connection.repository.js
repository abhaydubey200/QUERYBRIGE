"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConnectionRepository = void 0;
const pg_1 = require("pg");
const encryption_1 = require("../security/encryption");
const dotenv_1 = __importDefault(require("dotenv"));
dotenv_1.default.config();
const pool = new pg_1.Pool({
    connectionString: process.env.DATABASE_URL,
});
class ConnectionRepository {
    async create(config) {
        const encryptedPassword = config.password ? encryption_1.EncryptionService.encrypt(config.password) : '';
        const query = `
      INSERT INTO connections (name, type, host, port, username, password, database, schema_name, warehouse, ssl, timeout, pool_size)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
      RETURNING *
    `;
        const values = [
            config.name, config.type, config.host, config.port, config.username,
            encryptedPassword, config.database, config.schema, config.warehouse,
            config.ssl, config.timeout, config.poolSize
        ];
        const res = await pool.query(query, values);
        return res.rows[0];
    }
    async findAll() {
        const res = await pool.query('SELECT * FROM connections ORDER BY created_at DESC');
        return res.rows.map(row => this.sanitize(row));
    }
    async findById(id) {
        const res = await pool.query('SELECT * FROM connections WHERE id = $1', [id]);
        if (res.rows.length === 0)
            return null;
        return this.sanitize(res.rows[0]);
    }
    async updateHealth(id, status, latency) {
        await pool.query('UPDATE connections SET status = $1, latency_ms = $2, last_health_check = CURRENT_TIMESTAMP WHERE id = $3', [status, latency, id]);
    }
    async delete(id) {
        await pool.query('DELETE FROM connections WHERE id = $1', [id]);
    }
    /**
     * Decrypts password for connector use
     */
    async getFullConfig(id) {
        const res = await pool.query('SELECT * FROM connections WHERE id = $1', [id]);
        if (res.rows.length === 0)
            return null;
        const row = res.rows[0];
        return {
            id: row.id,
            name: row.name,
            type: row.type,
            host: row.host,
            port: row.port,
            username: row.username,
            password: encryption_1.EncryptionService.decrypt(row.password),
            database: row.database,
            schema: row.schema_name,
            warehouse: row.warehouse,
            ssl: row.ssl,
            timeout: row.timeout,
            poolSize: row.pool_size
        };
    }
    sanitize(row) {
        const { password, ...rest } = row;
        return rest;
    }
}
exports.ConnectionRepository = ConnectionRepository;
//# sourceMappingURL=connection.repository.js.map