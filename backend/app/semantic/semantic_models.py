from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID

class MetricBase(BaseModel):
    name: str
    description: Optional[str] = None
    formula: str
    metadata: Optional[Dict[str, Any]] = {}

class MetricCreate(MetricBase):
    connection_id: str

class MetricResponse(MetricBase):
    id: str
    connection_id: str

class DimensionBase(BaseModel):
    name: str
    description: Optional[str] = None
    column_name: str
    table_name: str

class DimensionCreate(DimensionBase):
    connection_id: str

class DimensionResponse(DimensionBase):
    id: str
    connection_id: str

class SemanticQuery(BaseModel):
    natural_language: str
    connection_id: str
