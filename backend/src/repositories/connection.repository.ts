import { Pool } from 'pg';
import { ConnectionConfig } from '../connectors/base.connector';
import { EncryptionService } from '../security/encryption';
import dotenv from 'dotenv';
import crypto from 'crypto';

dotenv.config();

let databaseUrl = process.env.DATABASE_URL || 'postgresql://admin:password123@localhost:5444/querybridge';

// Normalize URL: Remove '+asyncpg' which is Python-specific and not supported by node-postgres
databaseUrl = databaseUrl.replace('+asyncpg', '');

const pool = new Pool({
  connectionString: databaseUrl,
});

export class ConnectionRepository {
  async create(config: ConnectionConfig): Promise<any> {
    const encryptedPassword = config.password ? EncryptionService.encrypt(config.password) : '';
    
    const query = `
      INSERT INTO db_connections (
        id, name, db_type, host, port, username, password_encrypted, 
        database, advanced_settings, pool_settings, is_active, created_at
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, CURRENT_TIMESTAMP)
      RETURNING *
    `;
    
    const values = [
      crypto.randomUUID(),
      config.name, 
      config.type, 
      config.host, 
      config.port, 
      config.username, 
      encryptedPassword, 
      config.database,
      JSON.stringify(config.advanced_settings || {}),
      JSON.stringify({
        max_size: config.poolSize || 10,
        timeout: config.timeout || 30000
      }),
      true
    ];

    const res = await pool.query(query, values);
    return this.sanitize(res.rows[0]);
  }

  async findAll(): Promise<any[]> {
    const res = await pool.query('SELECT * FROM db_connections ORDER BY created_at DESC');
    return res.rows.map(row => this.sanitize(row));
  }

  async findById(id: string): Promise<any> {
    const res = await pool.query('SELECT * FROM db_connections WHERE id = $1', [id]);
    if (res.rows.length === 0) return null;
    return this.sanitize(res.rows[0]);
  }

  async updateHealth(id: string, status: string, latency: number): Promise<void> {
    await pool.query(
      'UPDATE db_connections SET status = $1, latency_ms = $2, last_heartbeat = CURRENT_TIMESTAMP WHERE id = $3',
      [status, latency, id]
    );
  }

  async delete(id: string): Promise<void> {
    await pool.query('DELETE FROM db_connections WHERE id = $1', [id]);
  }

  /**
   * Decrypts password for connector use
   */
  async getFullConfig(id: string): Promise<ConnectionConfig | null> {
    const res = await pool.query('SELECT * FROM db_connections WHERE id = $1', [id]);
    if (res.rows.length === 0) return null;
    
    const row = res.rows[0];
    const advanced = row.advanced_settings || {};
    const pool_settings = row.pool_settings || {};

    return {
      id: row.id,
      name: row.name,
      type: row.db_type,
      host: row.host,
      port: row.port,
      username: row.username,
      password: EncryptionService.decrypt(row.password_encrypted),
      database: row.database,
      schema: advanced.schema_name,
      ssl_mode: advanced.ssl_mode,
      advanced_settings: advanced,
      timeout: pool_settings.timeout,
      poolSize: pool_settings.max_size
    };
  }

  private sanitize(row: any) {
    const { password_encrypted, ...rest } = row;
    return rest;
  }
}
