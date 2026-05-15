"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BaseConnector = void 0;
/**
 * Abstract Base Connector
 */
class BaseConnector {
    config;
    constructor(config) {
        this.config = config;
    }
    async measureLatency(fn) {
        const start = Date.now();
        const result = await fn();
        const end = Date.now();
        return { result, latencyMs: end - start };
    }
}
exports.BaseConnector = BaseConnector;
//# sourceMappingURL=base.connector.js.map