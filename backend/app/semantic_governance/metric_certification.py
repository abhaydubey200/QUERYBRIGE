from sqlalchemy.orm import Session
from app.models.models import SemanticMetric
from typing import Dict, Any
import datetime

class MetricCertification:
    """Enterprise governance for business metrics."""
    
    def __init__(self, db: Session):
        self.db = db

    def certify_metric(self, metric_id: str, certifier_role: str):
        if certifier_role != "admin":
            return {"success": False, "error": "Only admins can certify metrics."}
            
        metric = self.db.query(SemanticMetric).filter(SemanticMetric.id == metric_id).first()
        if not metric:
            return {"success": False, "error": "Metric not found."}
            
        # Update metadata with certification status
        meta = metric.metadata_ or {}
        meta["is_certified"] = True
        meta["certified_at"] = str(datetime.datetime.utcnow())
        metric.metadata_ = meta
        
        self.db.commit()
        return {"success": True, "metric": metric.name}

    def calculate_trust_score(self, metric_id: str) -> float:
        """Calculate trust score based on lineage, certification, and usage."""
        metric = self.db.query(SemanticMetric).filter(SemanticMetric.id == metric_id).first()
        if not metric: return 0.0
        
        score = 50.0 # Base score
        if metric.metadata_.get("is_certified"): score += 30.0
        if metric.description: score += 10.0
        if metric.formula: score += 10.0
        
        return min(100.0, score)
