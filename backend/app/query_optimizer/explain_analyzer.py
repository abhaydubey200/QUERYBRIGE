from typing import List, Dict

class ExplainAnalyzer:
    def __init__(self):
        pass

    def analyze_plan(self, explain_json: List[Dict]):
        """Analyze a Postgres JSON explain plan for bottlenecks."""
        bottlenecks = []
        
        def traverse_nodes(node):
            # Check for Seq Scans on large tables
            if node.get("Node Type") == "Seq Scan":
                if node.get("Plan Rows", 0) > 10000:
                    bottlenecks.append({
                        "type": "Performance Risk",
                        "node": "Sequential Scan",
                        "table": node.get("Relation Name"),
                        "impact": "High",
                        "suggestion": f"Add an index to the columns used in the filter for table '{node.get('Relation Name')}'."
                    })
            
            # Check for Nested Loops on many rows
            if node.get("Node Type") == "Nested Loop":
                if node.get("Plan Rows", 0) > 1000:
                    bottlenecks.append({
                        "type": "Optimization Opportunity",
                        "node": "Nested Loop Join",
                        "impact": "Medium",
                        "suggestion": "Consider if a Hash Join would be more efficient by ensuring table statistics are up to date."
                    })

            # Recurse
            if "Plans" in node:
                for subplan in node["Plans"]:
                    traverse_nodes(subplan)

        for plan in explain_json:
            traverse_nodes(plan["Plan"])
            
        return bottlenecks
