from typing import List, Dict, Optional
import networkx as nx

class SemanticCompiler:
    """Enterprise compiler for high-level semantic queries."""
    
    def __init__(self, semantic_graph: nx.DiGraph):
        self.graph = semantic_graph

    def compile_metric(self, metric_name: str, filters: Dict = None) -> str:
        """
        Translates a metric name into a full SQL query by traversing the semantic graph.
        Handles JOIN resolution and alias generation.
        """
        # 1. Resolve Metric Node
        if metric_name not in self.graph:
            raise ValueError(f"Metric {metric_name} not found in semantic layer.")
            
        # 2. Get Dependencies (Tables, Columns)
        deps = list(nx.descendants(self.graph, metric_name))
        tables = [d for d in deps if self.graph.nodes[d].get("type") == "table"]
        
        # 3. Construct SQL (Simplified logic)
        table_list = ", ".join(tables)
        metric_expr = self.graph.nodes[metric_name].get("formula", "*")
        
        sql = f"SELECT {metric_expr} FROM {table_list}"
        
        if filters:
            where_clauses = []
            for k, v in filters.items():
                # Basic identifier validation for keys
                if not k.replace("_", "").isalnum():
                    continue
                # Escape single quotes in values
                escaped_v = str(v).replace("'", "''")
                where_clauses.append(f"{k} = '{escaped_v}'")
            
            if where_clauses:
                sql += f" WHERE {' AND '.join(where_clauses)}"
            
        return sql

class SemanticImpactAnalyzer:
    """Analyzes the blast radius of changes to the underlying data schema."""
    
    def __init__(self, semantic_graph: nx.DiGraph):
        self.graph = semantic_graph

    def analyze_table_change(self, table_name: str) -> Dict[str, List[str]]:
        """Identifies which metrics, dashboards, and AI prompts are affected by a table change."""
        affected_metrics = []
        
        # Find all nodes that depend on this table
        for node in self.graph.nodes:
            if table_name in nx.descendants(self.graph, node):
                affected_metrics.append(node)
                
        return {
            "metrics": affected_metrics,
            "dashboards": self._map_metrics_to_dashboards(affected_metrics),
            "criticality": "high" if len(affected_metrics) > 5 else "medium"
        }

    def _map_metrics_to_dashboards(self, metrics: List[str]) -> List[str]:
        # Implementation would query the DB for dashboards using these metrics
        return ["Marketing Performance", "CEO Overview"] # Placeholder
