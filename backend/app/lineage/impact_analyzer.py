"""
Impact Analyzer Service - Analyze blast radius and dependencies

Capabilities:
- Determine what breaks if table X is deleted
- Determine what depends on table X
- Calculate blast radius (1 hop, 2 hops, etc.)
- Find paths between tables
"""

import logging
from typing import List, Dict, Set, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.catalog_models import LineageEdge, CatalogTable
from collections import deque, defaultdict

logger = logging.getLogger(__name__)


class ImpactAnalyzer:
    """
    Analyzes data dependencies and impact of changes.
    
    Methods:
    - get_downstream_dependencies(table_id, depth)
    - get_upstream_dependencies(table_id, depth)
    - get_blast_radius(table_id)
    - get_change_impact(table_id, change_type)
    - find_path(source_id, target_id)
    - detect_cycles()
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_downstream_dependencies(self, table_id: str, depth: int = 5) -> Dict:
        """
        Find all tables that depend on this table (downstream).
        
        Example:
        - Table A (input)
        - Find all B where B <- A
        - Find all C where C <- B
        - Return tree: A → [B, D] → [C, E]
        """
        logger.info(f"Finding downstream dependencies for {table_id} (depth={depth})")
        
        # Build graph
        graph = await self._build_dependency_graph()
        
        # BFS to find downstream tables
        downstream = {}
        visited = set()
        queue = deque([(table_id, 0)])
        
        while queue:
            current_id, current_depth = queue.popleft()
            
            if current_depth > depth or current_id in visited:
                continue
            
            visited.add(current_id)
            
            # Find all tables that depend on current
            dependents = graph.get('downstream', {}).get(current_id, [])
            
            if current_depth not in downstream:
                downstream[current_depth] = []
            
            for dependent_id in dependents:
                downstream[current_depth].append(dependent_id)
                if dependent_id not in visited:
                    queue.append((dependent_id, current_depth + 1))
        
        # Format result
        result = {
            'table_id': table_id,
            'blast_radius': len(visited) - 1,  # Exclude self
            'downstream_by_level': downstream,
            'total_downstream': sum(len(v) for v in downstream.values()),
            'max_depth': max(downstream.keys()) if downstream else 0
        }
        
        logger.info(f"Downstream dependencies: {result['total_downstream']} tables")
        return result
    
    async def get_upstream_dependencies(self, table_id: str, depth: int = 5) -> Dict:
        """
        Find all tables that this table depends on (upstream).
        
        Example:
        - Table C (input)
        - Find all A, B where C depends on them
        - Find all X, Y where A depends on them
        - Return tree: C ← [A, B] ← [X, Y]
        """
        logger.info(f"Finding upstream dependencies for {table_id} (depth={depth})")
        
        # Build graph
        graph = await self._build_dependency_graph()
        
        # BFS to find upstream tables
        upstream = {}
        visited = set()
        queue = deque([(table_id, 0)])
        
        while queue:
            current_id, current_depth = queue.popleft()
            
            if current_depth > depth or current_id in visited:
                continue
            
            visited.add(current_id)
            
            # Find all tables that current depends on
            sources = graph.get('upstream', {}).get(current_id, [])
            
            if current_depth not in upstream:
                upstream[current_depth] = []
            
            for source_id in sources:
                upstream[current_depth].append(source_id)
                if source_id not in visited:
                    queue.append((source_id, current_depth + 1))
        
        # Format result
        result = {
            'table_id': table_id,
            'data_source_count': len(visited) - 1,
            'upstream_by_level': upstream,
            'total_upstream': sum(len(v) for v in upstream.values()),
            'max_depth': max(upstream.keys()) if upstream else 0
        }
        
        logger.info(f"Upstream dependencies: {result['total_upstream']} tables")
        return result
    
    async def get_blast_radius(self, table_id: str) -> Dict:
        """
        Calculate impact scope of deleting or modifying this table.
        
        Blast radius = how many tables would be affected?
        """
        logger.info(f"Calculating blast radius for {table_id}")
        
        # Get downstream (what would break)
        downstream = await self.get_downstream_dependencies(table_id, depth=10)
        
        # Get upstream (what we depend on)
        upstream = await self.get_upstream_dependencies(table_id, depth=10)
        
        # Calculate metrics
        direct_dependents = len(downstream['downstream_by_level'].get(1, []))
        indirect_dependents = sum(len(v) for k, v in downstream['downstream_by_level'].items() if k > 1)
        critical_path_length = downstream.get('max_depth', 0)
        
        # Estimate affected queries
        affected_queries_estimate = direct_dependents * 5 + indirect_dependents * 2  # Heuristic
        
        result = {
            'table_id': table_id,
            'direct_dependents': direct_dependents,
            'indirect_dependents': indirect_dependents,
            'total_dependents': direct_dependents + indirect_dependents,
            'critical_path_length': critical_path_length,
            'estimated_affected_queries': affected_queries_estimate,
            'data_sources': upstream['total_upstream'],
            'risk_level': self._calculate_risk_level(
                direct_dependents, 
                indirect_dependents, 
                critical_path_length
            ),
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }
        
        logger.info(f"Blast radius: {result['risk_level']} (direct={direct_dependents}, indirect={indirect_dependents})")
        return result
    
    async def get_change_impact(self, table_id: str, change_type: str) -> Dict:
        """
        Predict impact of specific change:
        - 'column_deleted': Column removed → breaks dependent queries
        - 'column_renamed': Column renamed → breaks dependent queries  
        - 'column_type_changed': Type changed → may break joins
        - 'row_deletion': Rows deleted → may break referential integrity
        - 'row_addition': New rows → may trigger cascades
        """
        logger.info(f"Analyzing impact of {change_type} on {table_id}")
        
        downstream = await self.get_downstream_dependencies(table_id, depth=5)
        
        impact_map = {
            'column_deleted': {'severity': 'high', 'description': 'Dependent queries will fail'},
            'column_renamed': {'severity': 'high', 'description': 'Dependent queries will fail'},
            'column_type_changed': {'severity': 'medium', 'description': 'Type mismatches in joins'},
            'row_deletion': {'severity': 'low', 'description': 'Referential integrity may be affected'},
            'row_addition': {'severity': 'low', 'description': 'Cascading updates may trigger'},
        }
        
        impact = impact_map.get(change_type, {'severity': 'unknown', 'description': 'Unknown impact'})
        
        result = {
            'table_id': table_id,
            'change_type': change_type,
            'severity': impact['severity'],
            'description': impact['description'],
            'affected_downstream_tables': downstream['total_downstream'],
            'affected_queries_estimate': downstream['total_downstream'] * 3,
            'affected_dashboards_estimate': downstream['total_downstream'] // 2,
            'recommendation': self._get_mitigation_recommendation(change_type, downstream['total_downstream'])
        }
        
        logger.info(f"Change impact: {impact['severity']} - {result['affected_downstream_tables']} tables affected")
        return result
    
    async def find_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """
        Find data flow path between two tables.
        
        Returns list: [source, intermediate1, intermediate2, ..., target]
        or None if no path exists.
        """
        logger.info(f"Finding path from {source_id} to {target_id}")
        
        graph = await self._build_dependency_graph()
        
        # BFS to find shortest path
        queue = deque([(source_id, [source_id])])
        visited = {source_id}
        
        while queue:
            current, path = queue.popleft()
            
            if current == target_id:
                return path
            
            # Find downstream (what current feeds into)
            next_tables = graph.get('downstream', {}).get(current, [])
            
            for next_id in next_tables:
                if next_id not in visited:
                    visited.add(next_id)
                    queue.append((next_id, path + [next_id]))
        
        logger.info("No path found between tables")
        return None
    
    async def detect_cycles(self) -> List[List[str]]:
        """
        Detect circular dependencies in lineage.
        
        Returns list of cycles (each cycle is a list of table IDs).
        """
        logger.info("Detecting cycles in lineage graph")
        
        graph = await self._build_dependency_graph()
        cycles = []
        
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get('downstream', {}).get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path[:])
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
            
            rec_stack.remove(node)
        
        # Check all nodes
        all_nodes = graph.get('all_nodes', set())
        for node in all_nodes:
            if node not in visited:
                dfs(node, [])
        
        if cycles:
            logger.warning(f"Found {len(cycles)} cycles in lineage graph")
        
        return cycles
    
    async def _build_dependency_graph(self) -> Dict:
        """
        Build graph from LineageEdge records.
        
        Returns:
        {
            'upstream': {table_id: [source_ids]},    # What this table depends on
            'downstream': {table_id: [target_ids]},  # What depends on this table
            'all_nodes': {table_ids}
        }
        """
        # Get all lineage edges
        stmt = select(LineageEdge).where(LineageEdge.is_active == True)
        result = await self.db.execute(stmt)
        edges = result.scalars().all()
        
        upstream = defaultdict(list)
        downstream = defaultdict(list)
        all_nodes = set()
        
        for edge in edges:
            upstream[edge.target_table_id].append(edge.source_table_id)
            downstream[edge.source_table_id].append(edge.target_table_id)
            all_nodes.add(edge.source_table_id)
            all_nodes.add(edge.target_table_id)
        
        return {
            'upstream': dict(upstream),
            'downstream': dict(downstream),
            'all_nodes': all_nodes
        }
    
    def _calculate_risk_level(self, direct: int, indirect: int, depth: int) -> str:
        """Calculate risk level based on impact metrics"""
        total_affected = direct + indirect
        
        if total_affected == 0:
            return 'LOW'
        elif depth <= 2 and total_affected <= 5:
            return 'LOW'
        elif depth <= 3 and total_affected <= 10:
            return 'MEDIUM'
        elif depth <= 5 and total_affected <= 20:
            return 'HIGH'
        else:
            return 'CRITICAL'
    
    def _get_mitigation_recommendation(self, change_type: str, affected_tables: int) -> str:
        """Get recommendation for mitigating change impact"""
        recommendations = {
            'column_deleted': f"Review {affected_tables} dependent tables before deletion. Consider deprecation period.",
            'column_renamed': f"Update {affected_tables} dependent queries. Use view aliasing for backward compatibility.",
            'column_type_changed': f"Verify {affected_tables} joins still work. Test data coercion.",
            'row_deletion': "Verify no foreign key constraints violated. Consider soft delete.",
            'row_addition': "Monitor cascading updates in {affected_tables} dependent tables.",
        }
        return recommendations.get(change_type, "Review impact carefully.")
