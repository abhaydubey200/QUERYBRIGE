from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import AuditLog, DBConnection, Dashboard
import re

class LineageEngine:
    """
    Analyzes audit logs and query history to build a data lineage graph.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_lineage(self, connection_id: str) -> Dict[str, Any]:
        # 1. Fetch recent successful queries for this connection
        logs = self.db.query(AuditLog).filter(
            AuditLog.resource_id == str(connection_id),
            AuditLog.action == "query_execution"
        ).all()

        nodes = []
        edges = []
        seen_tables = set()

        for log in logs:
            sql = log.metadata.get("sql", "")
            # Simple regex to extract table names (heuristic)
            tables = re.findall(r'FROM\s+([a-zA-Z0-9_.]+)', sql, re.IGNORECASE)
            
            query_node_id = f"q_{log.id}"
            nodes.append({
                "id": query_node_id,
                "type": "query",
                "data": {"label": f"Query: {sql[:20]}..."}
            })

            for table in tables:
                if table not in seen_tables:
                    nodes.append({
                        "id": table,
                        "type": "table",
                        "data": {"label": table}
                    })
                    seen_tables.add(table)
                
                edges.append({
                    "id": f"e_{table}_{query_node_id}",
                    "source": table,
                    "target": query_node_id
                })

        return {"nodes": nodes, "edges": edges}
