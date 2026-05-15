import CryptoJS from 'crypto-js';
import dotenv from 'dotenv';

dotenv.config();

const ENCRYPTION_KEY = process.env.ENCRYPTION_KEY || 'default-querybridge-secret-key-32-chars!!';

/**
 * Enterprise-grade encryption utility for sensitive data
 */
export class EncryptionService {
  /**
   * Encrypts a string using AES-256
   */
  static encrypt(text: string): string {
    return CryptoJS.AES.encrypt(text, ENCRYPTION_KEY).toString();
  }

  /**
   * Decrypts an AES-256 encrypted string
   */
  static decrypt(ciphertext: string): string {
    const bytes = CryptoJS.AES.decrypt(ciphertext, ENCRYPTION_KEY);
    const originalText = bytes.toString(CryptoJS.enc.Utf8);
    if (!originalText) {
      throw new Error('Failed to decrypt data: Invalid key or corrupted data');
    }
    return originalText;
  }

  /**
   * Securely masks sensitive info for logs
   */
  static mask(text: string): string {
    if (!text) return '';
    return text.length > 8 
      ? text.substring(0, 2) + '****' + text.substring(text.length - 2)
      : '********';
  }
}
