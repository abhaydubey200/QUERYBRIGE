/**
 * Enterprise-grade encryption utility for sensitive data
 */
export declare class EncryptionService {
    /**
     * Encrypts a string using AES-256
     */
    static encrypt(text: string): string;
    /**
     * Decrypts an AES-256 encrypted string
     */
    static decrypt(ciphertext: string): string;
    /**
     * Securely masks sensitive info for logs
     */
    static mask(text: string): string;
}
