import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class EvalTriggerRequest(BaseModel):
    notes: Optional[str] = None


class EvalRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    triggered_by: Optional[uuid.UUID] = None
    model_provider: str
    model_name: str
    faithfulness: Optional[float] = None
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None
    answer_relevancy: Optional[float] = None
    question_count: Optional[int] = None
    created_at: datetime


class EvalRunDetailResponse(EvalRunResponse):
    report_json: Optional[Dict[str, Any]] = None
