/**
 * SQL for Connection Metadata Storage
 */
export const CREATE_CONNECTIONS_TABLE = `
CREATE TABLE IF NOT EXISTS connections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  type VARCHAR(50) NOT NULL,
  host VARCHAR(255) NOT NULL,
  port INTEGER NOT NULL,
  username VARCHAR(255) NOT NULL,
  password TEXT NOT NULL, -- Encrypted
  database VARCHAR(255),
  schema_name VARCHAR(255),
  warehouse VARCHAR(255),
  ssl BOOLEAN DEFAULT FALSE,
  timeout INTEGER DEFAULT 5000,
  pool_size INTEGER DEFAULT 10,
  metadata JSONB DEFAULT '{}',
  last_health_check TIMESTAMP WITH TIME ZONE,
  status VARCHAR(50) DEFAULT 'unknown',
  latency_ms INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_connections_status ON connections(status);
CREATE INDEX IF NOT EXISTS idx_connections_type ON connections(type);
`;
