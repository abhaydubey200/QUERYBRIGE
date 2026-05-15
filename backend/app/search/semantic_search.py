"""
Semantic Search with Ranking

AI-powered metadata search that understands intent and ranks results.
Uses semantic similarity, popularity, and recency for ranking.
"""

from typing import List, Optional, Dict, Tuple
from uuid import UUID
from datetime import datetime
import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from pydantic import BaseModel

from app.models.catalog_models import (
    CatalogTable,
    CatalogColumn,
    DataProfile,
)

logger = logging.getLogger(__name__)


class SearchResult(BaseModel):
    """Search result with ranking information."""

    id: UUID
    resource_type: str  # "table", "column"
    name: str
    description: Optional[str] = None
    workspace_id: Optional[UUID] = None

    # Ranking
    relevance_score: float  # 0-1, semantic similarity
    popularity_score: float  # 0-1, based on usage
    recency_score: float  # 0-1, how recent
    combined_score: float  # weighted sum

    # Metadata
    owner: Optional[str] = None
    last_updated: Optional[datetime] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    matches: List[str] = []  # Which fields matched


class SemanticSearch:
    """Search metadata with semantic understanding and ranking."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        # Synonym mapping for query expansion
        self.synonyms = {
            "revenue": ["sales", "income", "earnings", "turnover"],
            "customer": ["client", "account", "consumer", "buyer"],
            "order": ["purchase", "transaction", "deal", "sale"],
            "product": ["item", "sku", "goods", "merchandise"],
            "employee": ["staff", "worker", "team member"],
            "department": ["division", "group", "section", "unit"],
            "date": ["time", "when", "period", "timestamp"],
        }

    # ============================================================================
    # PUBLIC METHODS
    # ============================================================================

    async def search(
        self,
        query: str,
        workspace_id: UUID,
        limit: int = 50,
        resource_types: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """
        Perform semantic search for metadata.

        Args:
            query: Search query
            workspace_id: Workspace ID
            limit: Maximum results
            resource_types: Optional filter (e.g., ["table", "column"])

        Returns:
            Ranked search results
        """
        try:
            if not query or len(query.strip()) == 0:
                return []

            logger.debug(f"Semantic search: '{query}' in workspace {workspace_id}")

            # Parse query
            query_terms = self._parse_query(query)

            # Search tables
            table_results = await self._search_tables(
                query_terms, workspace_id, limit
            )

            # Search columns
            column_results = await self._search_columns(
                query_terms, workspace_id, limit
            )

            # Combine and rank
            all_results = table_results + column_results

            # Rank results
            ranked = await self._rank_results(query, all_results)

            # Filter by type if specified
            if resource_types:
                ranked = [r for r in ranked if r.resource_type in resource_types]

            return ranked[:limit]
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []

    async def get_suggestions(self, query_prefix: str) -> List[str]:
        """
        Get search suggestions for autocomplete.

        Args:
            query_prefix: Prefix to search for

        Returns:
            List of suggestions
        """
        try:
            if not query_prefix or len(query_prefix.strip()) < 2:
                return []

            # Get matching table names
            tables = await self.db.scalars(
                select(CatalogTable.name).where(
                    CatalogTable.name.ilike(f"{query_prefix}%")
                ).limit(5)
            )

            # Get matching column names
            columns = await self.db.scalars(
                select(CatalogColumn.name).where(
                    CatalogColumn.name.ilike(f"{query_prefix}%")
                ).limit(5)
            )

            suggestions = list(set(list(tables) + list(columns)))
            return suggestions[:10]
        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
            return []

    # ============================================================================
    # PRIVATE METHODS - SEARCH
    # ============================================================================

    async def _search_tables(
        self, query_terms: List[str], workspace_id: UUID, limit: int
    ) -> List[SearchResult]:
        """Search for tables matching query."""
        results = []

        try:
            # Search by name
            for term in query_terms:
                tables = await self.db.scalars(
                    select(CatalogTable)
                    .where(
                        and_(
                            CatalogTable.workspace_id == workspace_id,
                            or_(
                                CatalogTable.name.ilike(f"%{term}%"),
                                CatalogTable.description.ilike(f"%{term}%"),
                            ),
                        )
                    )
                    .limit(limit)
                )

                for table in tables:
                    # Calculate relevance
                    relevance = self._calculate_relevance(
                        term, table.name, table.description
                    )

                    result = SearchResult(
                        id=table.id,
                        resource_type="table",
                        name=table.name,
                        description=table.description,
                        workspace_id=workspace_id,
                        relevance_score=relevance,
                        popularity_score=0.5,  # Will calculate later
                        recency_score=0.5,  # Will calculate later
                        combined_score=relevance,
                        owner=table.owner_id,
                        last_updated=table.created_at,
                        column_count=0,
                        matches=[term],
                    )

                    # Check if already in results
                    if not any(r.id == result.id for r in results):
                        results.append(result)

            return results
        except Exception as e:
            logger.error(f"Error searching tables: {e}")
            return []

    async def _search_columns(
        self, query_terms: List[str], workspace_id: UUID, limit: int
    ) -> List[SearchResult]:
        """Search for columns matching query."""
        results = []

        try:
            # Search by name
            for term in query_terms:
                columns = await self.db.scalars(
                    select(CatalogColumn)
                    .where(
                        CatalogColumn.name.ilike(f"%{term}%")
                    )
                    .limit(limit)
                )

                for column in columns:
                    # Get table for context
                    table = await self.db.scalar(
                        select(CatalogTable).where(
                            CatalogTable.id == column.table_id
                        )
                    )

                    relevance = self._calculate_relevance(
                        term, column.name, column.name
                    )

                    result = SearchResult(
                        id=column.id,
                        resource_type="column",
                        name=f"{table.name}.{column.name}" if table else column.name,
                        description=f"Column in {table.name}" if table else None,
                        workspace_id=workspace_id,
                        relevance_score=relevance,
                        popularity_score=0.5,
                        recency_score=0.5,
                        combined_score=relevance,
                        owner=table.owner_id if table else None,
                        last_updated=column.created_at,
                        matches=[term],
                    )

                    if not any(r.id == result.id for r in results):
                        results.append(result)

            return results
        except Exception as e:
            logger.error(f"Error searching columns: {e}")
            return []

    # ============================================================================
    # PRIVATE METHODS - RANKING
    # ============================================================================

    async def _rank_results(
        self, query: str, results: List[SearchResult]
    ) -> List[SearchResult]:
        """Rank search results."""
        try:
            for result in results:
                # Get popularity (query count)
                popularity = await self._get_popularity(result.id, result.resource_type)
                result.popularity_score = min(popularity / 1000, 1.0)  # Normalize

                # Get recency
                if result.last_updated:
                    days_old = (datetime.utcnow() - result.last_updated).days
                    result.recency_score = max(1.0 - (days_old / 365), 0)  # Decay over year
                else:
                    result.recency_score = 0.5

                # Calculate combined score
                result.combined_score = (
                    0.50 * result.relevance_score
                    + 0.30 * result.popularity_score
                    + 0.20 * result.recency_score
                )

            # Sort by combined score
            results.sort(key=lambda r: r.combined_score, reverse=True)
            return results
        except Exception as e:
            logger.error(f"Error ranking results: {e}")
            return sorted(results, key=lambda r: r.relevance_score, reverse=True)

    def _calculate_relevance(
        self, term: str, name: str, description: Optional[str]
    ) -> float:
        """Calculate relevance score for a match."""
        score = 0.0

        term_lower = term.lower()
        name_lower = name.lower()
        desc_lower = (description or "").lower()

        # Exact name match (highest)
        if term_lower == name_lower:
            score = 1.0

        # Exact word in name
        elif any(word == term_lower for word in name_lower.split("_")):
            score = 0.95

        # Name contains term
        elif term_lower in name_lower:
            score = 0.85

        # Description contains term
        elif term_lower in desc_lower:
            score = 0.60

        return score

    async def _get_popularity(
        self, resource_id: UUID, resource_type: str
    ) -> float:
        """Get popularity score (query count) for a resource."""
        try:
            # For now, return a default
            # In production, this would query a query_log table
            return 0.5
        except Exception:
            return 0.5

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _parse_query(self, query: str) -> List[str]:
        """Parse and expand query terms."""
        # Split query
        terms = query.lower().split()

        # Expand with synonyms
        expanded = set(terms)
        for term in terms:
            if term in self.synonyms:
                expanded.update(self.synonyms[term])

        return list(expanded)
