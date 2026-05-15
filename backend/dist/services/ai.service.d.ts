export declare class AIService {
    private static client;
    static analyzeSchema(schema: any): Promise<string>;
    static troubleshootConnection(error: string, config: any): Promise<string>;
}
