/**
 * QueryBridge AI Schema & Search API Client
 *
 * Provides typed access to Phase 3 AI services:
 * - Schema summarization
 * - Semantic entity mapping
 * - Relationship explanations
 * - Anomaly detection
 * - Semantic search
 * - Recommendations
 */

// Types
export interface SchemaSummary {
  table_id: string;
  summary: string;
  cached: boolean;
}

export interface SemanticEntity {
  table_id: string;
  entity_name: string;
  entity_type: 'fact' | 'dimension' | 'bridge';
  confidence: number;
  columns: Record<string, string>;
  metrics: Record<string, string>;
  dimensions: Record<string, string>;
  detected_by: string;
}

export interface TableMetrics {
  table_id: string;
  metrics: Record<string, string>;
}

export interface TableDimensions {
  table_id: string;
  dimensions: Record<string, string>;
}

export interface RelationshipExplanation {
  source_id: string;
  target_id: string;
  explanation: string;
}

export interface Anomaly {
  anomaly_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  baseline_value: number;
  current_value: number;
  deviation_pct: number;
  description: string;
  suggested_action: string;
}

export interface AnomaliesResponse {
  table_id: string;
  anomalies: Anomaly[];
  count: number;
}

export interface SearchResultItem {
  id: string;
  resource_type: 'table' | 'column';
  name: string;
  description?: string;
  relevance_score: number;
  popularity_score: number;
  recency_score: number;
  combined_score: number;
  matches: string[];
}

export interface SemanticSearchResponse {
  query: string;
  results: SearchResultItem[];
  count: number;
}

export interface SearchSuggestionsResponse {
  prefix: string;
  suggestions: string[];
}

export interface Recommendation {
  recommendation_type: string;
  resource_type: 'table' | 'column';
  resource_id: string;
  resource_name: string;
  title: string;
  description: string;
  suggested_action: string;
  severity: 'info' | 'warning' | 'critical';
}

export interface RecommendationsResponse {
  workspace_id: string;
  recommendations: Recommendation[];
  count: number;
  by_type: Record<string, number>;
}

// API Client
export class AiSchemaApiClient {
  private baseUrl: string;
  private headers: Record<string, string>;

  constructor(baseUrl: string = '/api/v1', token?: string) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Content-Type': 'application/json',
    };
    if (token) {
      this.headers['Authorization'] = `Bearer ${token}`;
    }
  }

  // ============================================================================
  // Schema Summarization
  // ============================================================================

  async summarizeTable(tableId: string, useCache: boolean = true): Promise<SchemaSummary> {
    const response = await fetch(
      `${this.baseUrl}/ai-schema/summarize/table/${tableId}?use_cache=${useCache}`,
      {
        method: 'GET',
        headers: this.headers,
      }
    );
    return this.handleResponse(response);
  }

  async summarizeColumn(columnId: string, useCache: boolean = true): Promise<{ column_id: string; summary: string }> {
    const response = await fetch(
      `${this.baseUrl}/ai-schema/summarize/column/${columnId}?use_cache=${useCache}`,
      {
        method: 'GET',
        headers: this.headers,
      }
    );
    return this.handleResponse(response);
  }

  async batchSummarizeTables(tableIds: string[]): Promise<Record<string, string>> {
    const response = await fetch(`${this.baseUrl}/ai-schema/summarize/batch`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(tableIds),
    });
    return this.handleResponse(response);
  }

  // ============================================================================
  // Semantic Entity Mapping
  // ============================================================================

  async getSemanticEntity(tableId: string): Promise<SemanticEntity> {
    const response = await fetch(
      `${this.baseUrl}/ai-schema/entity/${tableId}`,
      {
        method: 'GET',
        headers: this.headers,
      }
    );
    return this.handleResponse(response);
  }

  async getTableMetrics(tableId: string): Promise<TableMetrics> {
    const response = await fetch(
      `${this.baseUrl}/ai-schema/metrics/${tableId}`,
      {
        method: 'GET',
        headers: this.headers,
      }
    );
    return this.handleResponse(response);
  }

  async getTableDimensions(tableId: string): Promise<TableDimensions> {
    const response = await fetch(
      `${this.baseUrl}/ai-schema/dimensions/${tableId}`,
      {
        method: 'GET',
        headers: this.headers,
      }
    );
    return this.handleResponse(response);
  }

  // ============================================================================
  // Relationship Explanations
  // ============================================================================

  async explainRelationship(sourceId: string, targetId: string): Promise<RelationshipExplanation> {
    const response = await fetch(
      `${this.baseUrl}/ai-schema/relationships/explain/${sourceId}/${targetId}`,
      {
        method: 'GET',
        headers: this.headers,
      }
    );
    return this.handleResponse(response);
  }

  // ============================================================================
  // Anomaly Detection
  // ============================================================================

  async getTableAnomalies(tableId: string, lookbackDays: number = 30): Promise<AnomaliesResponse> {
    const response = await fetch(
      `${this.baseUrl}/quality/anomalies/${tableId}?lookback_days=${lookbackDays}`,
      {
        method: 'GET',
        headers: this.headers,
      }
    );
    return this.handleResponse(response);
  }

  // ============================================================================
  // Semantic Search
  // ============================================================================

  async search(
    query: string,
    workspaceId: string,
    limit: number = 50,
    resourceTypes?: string[]
  ): Promise<SemanticSearchResponse> {
    const params = new URLSearchParams({
      query,
      workspace_id: workspaceId,
      limit: limit.toString(),
    });

    if (resourceTypes) {
      resourceTypes.forEach((type) => params.append('resource_types', type));
    }

    const response = await fetch(`${this.baseUrl}/search/semantic?${params}`, {
      method: 'POST',
      headers: this.headers,
    });
    return this.handleResponse(response);
  }

  async getSearchSuggestions(prefix: string): Promise<SearchSuggestionsResponse> {
    const params = new URLSearchParams({ prefix });
    const response = await fetch(`${this.baseUrl}/search/suggestions?${params}`, {
      method: 'GET',
      headers: this.headers,
    });
    return this.handleResponse(response);
  }

  // ============================================================================
  // Recommendations
  // ============================================================================

  async getWorkspaceRecommendations(
    workspaceId: string,
    limit: number = 100,
    severity?: string
  ): Promise<RecommendationsResponse> {
    const params = new URLSearchParams({
      limit: limit.toString(),
    });

    if (severity) {
      params.append('severity', severity);
    }

    const response = await fetch(
      `${this.baseUrl}/recommendations/workspace/${workspaceId}?${params}`,
      {
        method: 'GET',
        headers: this.headers,
      }
    );
    return this.handleResponse(response);
  }

  async getResourceRecommendations(resourceId: string): Promise<RecommendationsResponse> {
    const response = await fetch(
      `${this.baseUrl}/recommendations/resource/${resourceId}`,
      {
        method: 'GET',
        headers: this.headers,
      }
    );
    return this.handleResponse(response);
  }

  // ============================================================================
  // Health Check
  // ============================================================================

  async healthCheck(): Promise<{ status: string; services: Record<string, string> }> {
    const response = await fetch(`${this.baseUrl}/health/ai-schema`, {
      method: 'GET',
      headers: this.headers,
    });
    return this.handleResponse(response);
  }

  // ============================================================================
  // Helpers
  // ============================================================================

  private async handleResponse(response: Response): Promise<any> {
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `API Error: ${response.statusText}`);
    }
    return response.json();
  }
}

// Singleton instance
let apiClient: AiSchemaApiClient;

export function getApiClient(baseUrl?: string, token?: string): AiSchemaApiClient {
  if (!apiClient) {
    apiClient = new AiSchemaApiClient(baseUrl, token);
  }
  return apiClient;
}

// React Hook for API client
export function useAiSchemaApi() {
  return getApiClient();
}
