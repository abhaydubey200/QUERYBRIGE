"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.EncryptionService = void 0;
const crypto_js_1 = __importDefault(require("crypto-js"));
const dotenv_1 = __importDefault(require("dotenv"));
dotenv_1.default.config();
const ENCRYPTION_KEY = process.env.ENCRYPTION_KEY || 'default-querybridge-secret-key-32-chars!!';
/**
 * Enterprise-grade encryption utility for sensitive data
 */
class EncryptionService {
    /**
     * Encrypts a string using AES-256
     */
    static encrypt(text) {
        return crypto_js_1.default.AES.encrypt(text, ENCRYPTION_KEY).toString();
    }
    /**
     * Decrypts an AES-256 encrypted string
     */
    static decrypt(ciphertext) {
        const bytes = crypto_js_1.default.AES.decrypt(ciphertext, ENCRYPTION_KEY);
        const originalText = bytes.toString(crypto_js_1.default.enc.Utf8);
        if (!originalText) {
            throw new Error('Failed to decrypt data: Invalid key or corrupted data');
        }
        return originalText;
    }
    /**
     * Securely masks sensitive info for logs
     */
    static mask(text) {
        if (!text)
            return '';
        return text.length > 8
            ? text.substring(0, 2) + '****' + text.substring(text.length - 2)
            : '********';
    }
}
exports.EncryptionService = EncryptionService;
//# sourceMappingURL=encryption.js.map