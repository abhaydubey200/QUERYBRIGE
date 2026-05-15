"""
Phase 3 AI/Semantic Services API Endpoints

Exposes all Phase 3 services (schema summarization, semantic mapping, 
anomaly detection, semantic search, recommendations) via FastAPI.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db as get_db_session
from app.ai_schema.schema_summarizer import SchemaSummarizer
from app.ai_schema.semantic_mapper import SemanticMapper, SemanticEntity
from app.ai_schema.relationship_explainer import RelationshipExplainer
from app.profiling.anomaly_detector import AnomalyDetector, Anomaly
from app.search.semantic_search import SemanticSearch, SearchResult
from app.governance.recommendation_engine import RecommendationEngine, MetadataRecommendation

router = APIRouter(prefix="/api/v1", tags=["AI Schema & Search"])


# ============================================================================
# SCHEMA SUMMARIZATION ENDPOINTS
# ============================================================================

@router.get("/ai-schema/summarize/table/{table_id}")
async def summarize_table(
    table_id: UUID,
    use_cache: bool = True,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Generate AI-powered summary for a table.

    Args:
        table_id: Table ID to summarize
        use_cache: Whether to use cached summary

    Returns:
        {
            "table_id": UUID,
            "name": str,
            "summary": str
        }
    """
    try:
        summarizer = SchemaSummarizer(db)
        summary = await summarizer.summarize_table(table_id, use_cache=use_cache)

        return {
            "table_id": str(table_id),
            "summary": summary,
            "cached": use_cache,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error summarizing table: {str(e)}")


@router.get("/ai-schema/summarize/column/{column_id}")
async def summarize_column(
    column_id: UUID,
    use_cache: bool = True,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Generate AI-powered summary for a column.

    Args:
        column_id: Column ID to summarize
        use_cache: Whether to use cached summary

    Returns:
        {
            "column_id": UUID,
            "summary": str
        }
    """
    try:
        summarizer = SchemaSummarizer(db)
        summary = await summarizer.summarize_column(column_id, use_cache=use_cache)

        return {
            "column_id": str(column_id),
            "summary": summary,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error summarizing column: {str(e)}")


@router.post("/ai-schema/summarize/batch")
async def batch_summarize_tables(
    table_ids: List[UUID],
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Batch summarize multiple tables.

    Args:
        table_ids: List of table IDs

    Returns:
        {
            "table_id": summary,
            ...
        }
    """
    try:
        summarizer = SchemaSummarizer(db)
        results = await summarizer.batch_summarize_tables(table_ids)

        return {
            str(table_id): summary
            for table_id, summary in results.items()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in batch summarization: {str(e)}")


# ============================================================================
# SEMANTIC ENTITY ENDPOINTS
# ============================================================================

@router.get("/ai-schema/entity/{table_id}")
async def get_semantic_entity(
    table_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get semantic entity mapping for a table.

    Returns:
        {
            "table_id": UUID,
            "entity_name": str,
            "entity_type": str,  # "fact", "dimension", "bridge"
            "confidence": float,
            "columns": {...},
            "metrics": {...},
            "dimensions": {...}
        }
    """
    try:
        mapper = SemanticMapper(db)
        entity = await mapper.map_table_to_entity(table_id)

        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")

        return {
            "table_id": str(table_id),
            "entity_name": entity.entity_name,
            "entity_type": entity.entity_type,
            "confidence": entity.confidence,
            "columns": entity.columns,
            "metrics": entity.metrics,
            "dimensions": entity.dimensions,
            "detected_by": entity.detected_by,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting entity: {str(e)}")


@router.get("/ai-schema/metrics/{table_id}")
async def get_table_metrics(
    table_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get detected metrics for a table.

    Returns:
        {
            "metric_name": "aggregation_type",
            ...
        }
    """
    try:
        mapper = SemanticMapper(db)
        metrics = await mapper.detect_metrics(table_id)

        return {
            "table_id": str(table_id),
            "metrics": metrics,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}")


@router.get("/ai-schema/dimensions/{table_id}")
async def get_table_dimensions(
    table_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get detected dimensions for a table.

    Returns:
        {
            "dimension_name": "dimension_type",
            ...
        }
    """
    try:
        mapper = SemanticMapper(db)
        dimensions = await mapper.detect_dimensions(table_id)

        return {
            "table_id": str(table_id),
            "dimensions": dimensions,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dimensions: {str(e)}")


# ============================================================================
# RELATIONSHIP EXPLANATION ENDPOINTS
# ============================================================================

@router.get("/ai-schema/relationships/explain/{source_id}/{target_id}")
async def explain_relationship(
    source_id: UUID,
    target_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get human-readable explanation for a relationship.

    Returns:
        {
            "source_id": UUID,
            "target_id": UUID,
            "explanation": str
        }
    """
    try:
        explainer = RelationshipExplainer(db)
        explanation = await explainer.explain_relationship(source_id, target_id)

        return {
            "source_id": str(source_id),
            "target_id": str(target_id),
            "explanation": explanation,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error explaining relationship: {str(e)}"
        )


# ============================================================================
# ANOMALY DETECTION ENDPOINTS
# ============================================================================

@router.get("/quality/anomalies/{table_id}")
async def get_table_anomalies(
    table_id: UUID,
    lookback_days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get detected anomalies for a table.

    Args:
        table_id: Table ID
        lookback_days: Days to look back for anomalies (1-365)

    Returns:
        {
            "table_id": UUID,
            "anomalies": [
                {
                    "anomaly_type": str,
                    "severity": str,
                    "baseline_value": float,
                    "current_value": float,
                    "deviation_pct": float,
                    "description": str,
                    "suggested_action": str
                }
            ]
        }
    """
    try:
        detector = AnomalyDetector(db)
        anomalies = await detector.detect_anomalies(table_id, lookback_days)

        return {
            "table_id": str(table_id),
            "anomalies": [
                {
                    "anomaly_type": a.anomaly_type,
                    "severity": a.severity,
                    "baseline_value": a.baseline_value,
                    "current_value": a.current_value,
                    "deviation_pct": a.deviation_pct,
                    "description": a.description,
                    "suggested_action": a.suggested_action,
                }
                for a in anomalies
            ],
            "count": len(anomalies),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error detecting anomalies: {str(e)}"
        )


# ============================================================================
# SEMANTIC SEARCH ENDPOINTS
# ============================================================================

@router.post("/search/semantic")
async def semantic_search(
    query: str = Query(..., min_length=2, max_length=100),
    workspace_id: UUID = Query(...),
    limit: int = Query(50, ge=1, le=500),
    resource_types: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Perform semantic search on metadata.

    Args:
        query: Search query
        workspace_id: Workspace ID
        limit: Maximum results (1-500)
        resource_types: Optional filter (["table", "column"])

    Returns:
        {
            "query": str,
            "results": [
                {
                    "id": UUID,
                    "resource_type": str,
                    "name": str,
                    "combined_score": float,
                    ...
                }
            ],
            "count": int
        }
    """
    try:
        searcher = SemanticSearch(db)
        results = await searcher.search(
            query,
            workspace_id,
            limit=limit,
            resource_types=resource_types,
        )

        return {
            "query": query,
            "results": [
                {
                    "id": str(r.id),
                    "resource_type": r.resource_type,
                    "name": r.name,
                    "description": r.description,
                    "relevance_score": r.relevance_score,
                    "popularity_score": r.popularity_score,
                    "recency_score": r.recency_score,
                    "combined_score": r.combined_score,
                    "matches": r.matches,
                }
                for r in results
            ],
            "count": len(results),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in semantic search: {str(e)}"
        )


@router.get("/search/suggestions")
async def get_search_suggestions(
    prefix: str = Query(..., min_length=1, max_length=50),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get search suggestions for autocomplete.

    Args:
        prefix: Search prefix

    Returns:
        {
            "prefix": str,
            "suggestions": [str, ...]
        }
    """
    try:
        searcher = SemanticSearch(db)
        suggestions = await searcher.get_suggestions(prefix)

        return {
            "prefix": prefix,
            "suggestions": suggestions,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting suggestions: {str(e)}"
        )


# ============================================================================
# RECOMMENDATION ENDPOINTS
# ============================================================================

@router.get("/recommendations/workspace/{workspace_id}")
async def get_workspace_recommendations(
    workspace_id: UUID,
    limit: int = Query(100, ge=1, le=500),
    severity: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get all recommendations for a workspace.

    Args:
        workspace_id: Workspace ID
        limit: Maximum results
        severity: Optional filter (info, warning, critical)

    Returns:
        {
            "workspace_id": UUID,
            "recommendations": [
                {
                    "recommendation_type": str,
                    "resource_id": UUID,
                    "resource_name": str,
                    "title": str,
                    "description": str,
                    "severity": str
                }
            ],
            "count": int,
            "by_type": {...}
        }
    """
    try:
        engine = RecommendationEngine(db)
        recommendations = await engine.generate_recommendations(workspace_id)

        # Filter by severity if specified
        if severity:
            recommendations = [r for r in recommendations if r.severity == severity]

        # Limit results
        recommendations = recommendations[:limit]

        # Group by type
        by_type = {}
        for rec in recommendations:
            rec_type = rec.recommendation_type
            by_type[rec_type] = by_type.get(rec_type, 0) + 1

        return {
            "workspace_id": str(workspace_id),
            "recommendations": [
                {
                    "recommendation_type": r.recommendation_type,
                    "resource_type": r.resource_type,
                    "resource_id": str(r.resource_id),
                    "resource_name": r.resource_name,
                    "title": r.title,
                    "description": r.description,
                    "suggested_action": r.suggested_action,
                    "severity": r.severity,
                }
                for r in recommendations
            ],
            "count": len(recommendations),
            "by_type": by_type,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting recommendations: {str(e)}"
        )


@router.get("/recommendations/resource/{resource_id}")
async def get_resource_recommendations(
    resource_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get recommendations for a specific resource.

    Args:
        resource_id: Resource ID (table, column, etc.)

    Returns:
        {
            "resource_id": UUID,
            "recommendations": [...]
        }
    """
    try:
        engine = RecommendationEngine(db)
        recommendations = await engine.get_recommendations_for_resource(resource_id)

        return {
            "resource_id": str(resource_id),
            "recommendations": [
                {
                    "recommendation_type": r.recommendation_type,
                    "title": r.title,
                    "description": r.description,
                    "suggested_action": r.suggested_action,
                    "severity": r.severity,
                }
                for r in recommendations
            ],
            "count": len(recommendations),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting recommendations: {str(e)}"
        )


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health/ai-schema")
async def health_check() -> dict:
    """
    Health check for AI schema services.

    Returns:
        {
            "status": "healthy",
            "services": {
                "schema_summarizer": "ready",
                "semantic_mapper": "ready",
                "relationship_explainer": "ready",
                "anomaly_detector": "ready",
                "semantic_search": "ready",
                "recommendation_engine": "ready"
            }
        }
    """
    return {
        "status": "healthy",
        "services": {
            "schema_summarizer": "ready",
            "semantic_mapper": "ready",
            "relationship_explainer": "ready",
            "anomaly_detector": "ready",
            "semantic_search": "ready",
            "recommendation_engine": "ready",
        },
    }
