"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AIService = void 0;
const axios_1 = __importDefault(require("axios"));
const dotenv_1 = __importDefault(require("dotenv"));
dotenv_1.default.config();
const NVIDIA_API_KEY = process.env.NVIDIA_API_KEY;
const MODEL = 'qwen/qwen3-coder-480b-a35b-instruct';
class AIService {
    static client = axios_1.default.create({
        baseURL: 'https://integrate.api.nvidia.com/v1',
        headers: {
            'Authorization': `Bearer ${NVIDIA_API_KEY}`,
            'Content-Type': 'application/json',
        },
    });
    static async analyzeSchema(schema) {
        try {
            const prompt = `
        Analyze the following database schema and provide insights:
        1. List main entities.
        2. Identify potential relationships (PK/FK).
        3. Suggest performance optimizations (indexes).
        4. Explain the purpose of this data if possible.

        Schema:
        ${JSON.stringify(schema, null, 2)}
      `;
            const response = await this.client.post('/chat/completions', {
                model: MODEL,
                messages: [{ role: 'user', content: prompt }],
                temperature: 0.1,
                max_tokens: 1024,
            });
            return response.data.choices[0].message.content;
        }
        catch (error) {
            console.error('AI Schema Analysis failed:', error.message);
            return 'AI assistance temporarily unavailable.';
        }
    }
    static async troubleshootConnection(error, config) {
        try {
            const prompt = `
        A user is trying to connect to a database but failed with the following error:
        Error: ${error}
        
        Connection Config:
        Type: ${config.type}
        Host: ${config.host}
        Port: ${config.port}
        Database: ${config.database}

        Suggest 3 potential fixes for this issue.
      `;
            const response = await this.client.post('/chat/completions', {
                model: MODEL,
                messages: [{ role: 'user', content: prompt }],
            });
            return response.data.choices[0].message.content;
        }
        catch (error) {
            return 'Unable to troubleshoot at this time.';
        }
    }
}
exports.AIService = AIService;
//# sourceMappingURL=ai.service.js.map