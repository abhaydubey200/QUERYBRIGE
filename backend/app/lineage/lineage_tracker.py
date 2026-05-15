"""
Lineage Tracker Service - Extract data dependencies from queries and procedures

Tracks:
- Source tables → Target tables (query lineage)
- Column-level lineage (which source cols → target col)
- Transformation logic
- Confidence scoring
"""

import re
import logging
from typing import List, Dict, Optional, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.catalog_models import LineageEdge, CatalogTable, CatalogColumn
import uuid
import datetime

logger = logging.getLogger(__name__)


class LineageTracker:
    """
    Extracts lineage from SQL queries and procedures.
    
    Supports:
    - SELECT INTO / CREATE TABLE AS SELECT (CTAS)
    - INSERT INTO ... SELECT
    - UPDATE ... FROM (Postgres/MSSQL style)
    - Stored procedure analysis
    - Manual lineage definition
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def track_query_lineage(self, query: str, connection_id: str, 
                                  discovered_by: str = "sql_parser") -> List[Dict]:
        """
        Parse SQL query and extract source → target dependencies.
        
        Returns list of discovered lineage edges.
        """
        logger.info(f"Tracking lineage for query (length={len(query)})")
        
        try:
            # Normalize query
            query_upper = query.upper().strip()
            
            # Determine lineage pattern
            lineage_edges = []
            
            # Pattern 1: CREATE TABLE ... AS SELECT
            if query_upper.startswith('CREATE TABLE'):
                edges = await self._extract_ctas_lineage(query, connection_id, discovered_by)
                lineage_edges.extend(edges)
            
            # Pattern 2: INSERT INTO ... SELECT
            elif query_upper.startswith('INSERT INTO'):
                edges = await self._extract_insert_select_lineage(query, connection_id, discovered_by)
                lineage_edges.extend(edges)
            
            # Pattern 3: UPDATE ... FROM (Postgres/MSSQL)
            elif query_upper.startswith('UPDATE'):
                edges = await self._extract_update_from_lineage(query, connection_id, discovered_by)
                lineage_edges.extend(edges)
            
            # Pattern 4: SELECT (no explicit target, just dependency analysis)
            elif query_upper.startswith('SELECT'):
                # For SELECT, we identify source tables but no target
                # This is useful for impact analysis: "if this SELECT fails, what breaks?"
                sources = self._extract_source_tables(query)
                logger.debug(f"Found SELECT from tables: {sources}")
            
            logger.info(f"Discovered {len(lineage_edges)} lineage edges")
            return lineage_edges
            
        except Exception as e:
            logger.error(f"Lineage extraction failed: {str(e)}")
            raise
    
    async def _extract_ctas_lineage(self, query: str, connection_id: str, 
                                   discovered_by: str) -> List[Dict]:
        """Extract lineage from CREATE TABLE ... AS SELECT"""
        target_table = self._extract_create_table_name(query)
        source_tables = self._extract_source_tables(query)
        
        edges = []
        for source_table in source_tables:
            edge = {
                'connection_id': connection_id,
                'source_table_name': source_table,
                'target_table_name': target_table,
                'lineage_type': 'transform',
                'discovery_method': discovered_by,
                'transformation_logic': 'CREATE TABLE AS SELECT',
                'query_template': query[:200],  # First 200 chars as sample
                'confidence': 0.95
            }
            edges.append(edge)
            await self._create_lineage_edge(edge)
        
        return edges
    
    async def _extract_insert_select_lineage(self, query: str, connection_id: str,
                                            discovered_by: str) -> List[Dict]:
        """Extract lineage from INSERT INTO table SELECT"""
        match = re.search(r'INSERT\s+INTO\s+([^\s(]+)', query, re.IGNORECASE)
        if not match:
            return []
        
        target_table = match.group(1).strip()
        source_tables = self._extract_source_tables(query)
        
        edges = []
        for source_table in source_tables:
            edge = {
                'connection_id': connection_id,
                'source_table_name': source_table,
                'target_table_name': target_table,
                'lineage_type': 'direct',
                'discovery_method': discovered_by,
                'transformation_logic': 'INSERT INTO ... SELECT',
                'query_template': query[:200],
                'confidence': 0.95
            }
            edges.append(edge)
            await self._create_lineage_edge(edge)
        
        return edges
    
    async def _extract_update_from_lineage(self, query: str, connection_id: str,
                                          discovered_by: str) -> List[Dict]:
        """Extract lineage from UPDATE table SET ... FROM source"""
        match = re.search(r'UPDATE\s+([^\s]+)', query, re.IGNORECASE)
        if not match:
            return []
        
        target_table = match.group(1).strip()
        source_tables = self._extract_source_tables(query)
        
        edges = []
        for source_table in source_tables:
            if source_table.upper() != target_table.upper():  # Don't self-reference
                edge = {
                    'connection_id': connection_id,
                    'source_table_name': source_table,
                    'target_table_name': target_table,
                    'lineage_type': 'join',
                    'discovery_method': discovered_by,
                    'transformation_logic': 'UPDATE ... FROM',
                    'query_template': query[:200],
                    'confidence': 0.85
                }
                edges.append(edge)
                await self._create_lineage_edge(edge)
        
        return edges
    
    def _extract_create_table_name(self, query: str) -> str:
        """Extract target table name from CREATE TABLE statement"""
        match = re.search(r'CREATE\s+(?:TEMPORARY\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([^\s(]+)', 
                         query, re.IGNORECASE)
        return match.group(1).strip() if match else "UNKNOWN"
    
    def _extract_source_tables(self, query: str) -> Set[str]:
        """
        Extract all source tables from SQL query.
        
        Handles:
        - FROM table
        - JOIN table
        - UNION SELECT FROM table
        - Subqueries (basic)
        """
        tables = set()
        
        # Remove comments
        query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        
        # Pattern: FROM table or JOIN table
        # Captures: FROM|JOIN table_name or FROM|JOIN (subquery) AS alias
        pattern = r'(?:FROM|JOIN)\s+(?:\(.*?\)\s+[AS\s]*)?([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)'
        
        for match in re.finditer(pattern, query, re.IGNORECASE):
            table_name = match.group(1).strip()
            # Skip subqueries and non-table references
            if not table_name.upper() in ['SELECT', 'WITH', 'VALUES']:
                tables.add(table_name)
        
        return tables
    
    async def _create_lineage_edge(self, edge_data: Dict) -> LineageEdge:
        """Create a lineage edge in the database"""
        try:
            # Find or create tables
            source_stmt = select(CatalogTable).where(
                CatalogTable.table_name == edge_data['source_table_name']
            )
            source_result = await self.db.execute(source_stmt)
            source_table = source_result.scalar_one_or_none()
            
            target_stmt = select(CatalogTable).where(
                CatalogTable.table_name == edge_data['target_table_name']
            )
            target_result = await self.db.execute(target_stmt)
            target_table = target_result.scalar_one_or_none()
            
            if not source_table or not target_table:
                logger.debug(f"Source or target table not found: {edge_data}")
                return None
            
            # Check if edge already exists
            existing = select(LineageEdge).where(
                (LineageEdge.source_table_id == source_table.id) &
                (LineageEdge.target_table_id == target_table.id) &
                (LineageEdge.discovery_method == edge_data['discovery_method'])
            )
            result = await self.db.execute(existing)
            if result.scalar_one_or_none():
                logger.debug(f"Lineage edge already exists")
                return None
            
            # Create edge
            lineage_edge = LineageEdge(
                id=str(uuid.uuid4()),
                connection_id=edge_data['connection_id'],
                source_table_id=source_table.id,
                target_table_id=target_table.id,
                lineage_type=edge_data['lineage_type'],
                discovery_method=edge_data['discovery_method'],
                transformation_logic=edge_data['transformation_logic'],
                query_template=edge_data['query_template'],
                confidence=edge_data['confidence'],
                is_active=True,
                created_at=datetime.datetime.utcnow(),
                discovered_by="system"
            )
            self.db.add(lineage_edge)
            await self.db.commit()
            
            logger.debug(f"Created lineage edge: {source_table.table_name} → {target_table.table_name}")
            return lineage_edge
            
        except Exception as e:
            logger.error(f"Failed to create lineage edge: {str(e)}")
            return None
    
    async def add_manual_lineage(self, source_table_id: str, target_table_id: str,
                                 transformation_logic: str, connection_id: str) -> LineageEdge:
        """
        Allow manual lineage definition.
        Useful for tracking lineage through external systems or manual ETL.
        """
        # Check if edge already exists
        existing = select(LineageEdge).where(
            (LineageEdge.source_table_id == source_table_id) &
            (LineageEdge.target_table_id == target_table_id)
        )
        result = await self.db.execute(existing)
        if result.scalar_one_or_none():
            logger.info("Lineage edge already exists")
            return None
        
        edge = LineageEdge(
            id=str(uuid.uuid4()),
            connection_id=connection_id,
            source_table_id=source_table_id,
            target_table_id=target_table_id,
            lineage_type='transform',
            discovery_method='manual',
            transformation_logic=transformation_logic,
            confidence=1.0,
            is_active=True,
            created_at=datetime.datetime.utcnow(),
            discovered_by="manual"
        )
        self.db.add(edge)
        await self.db.commit()
        
        logger.info(f"Added manual lineage edge: {source_table_id} → {target_table_id}")
        return edge
    
    async def extract_column_lineage(self, query: str, target_column: str) -> Dict:
        """
        Track which source columns → target column.
        
        Example: orders.amount + orders.tax → revenue_report.total_revenue
        
        This is more complex and requires expression parsing.
        For Phase 2, we'll store basic column mappings.
        """
        logger.info(f"Extracting column lineage for {target_column}")
        
        # Simple approach: extract SELECT clause to identify source columns
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query, re.IGNORECASE | re.DOTALL)
        if not select_match:
            return {}
        
        select_clause = select_match.group(1)
        source_columns = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*\.)?([a-zA-Z_][a-zA-Z0-9_]*)', select_clause)
        
        return {
            'target_column': target_column,
            'source_columns': source_columns,
            'query_fragment': select_clause[:100]
        }
