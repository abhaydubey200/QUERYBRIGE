import { ConnectionConfig } from '../connectors/base.connector';
export declare class ConnectionRepository {
    create(config: ConnectionConfig): Promise<any>;
    findAll(): Promise<any[]>;
    findById(id: string): Promise<any>;
    updateHealth(id: string, status: string, latency: number): Promise<void>;
    delete(id: string): Promise<void>;
    /**
     * Decrypts password for connector use
     */
    getFullConfig(id: string): Promise<ConnectionConfig | null>;
    private sanitize;
}
