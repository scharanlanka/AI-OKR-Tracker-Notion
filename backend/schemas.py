from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class KeyResultOut(BaseModel):
    id: int
    notion_id: str
    objective_id: int
    title: str
    owner: Optional[str] = None
    status: Optional[str] = None
    progress: float = 0.0
    deadline: Optional[date] = None
    is_blocked: bool = False
    blocker_notes: Optional[str] = None

    class Config:
        from_attributes = True


class ObjectiveOut(BaseModel):
    id: int
    notion_id: str
    title: str
    owner: Optional[str] = None
    status: Optional[str] = None
    progress: float = 0.0
    target_date: Optional[date] = None
    key_results: list[KeyResultOut] = []

    class Config:
        from_attributes = True


class RiskItem(BaseModel):
    objective_title: str
    key_result_title: str
    owner: Optional[str]
    progress: float
    status: Optional[str]
    deadline: Optional[date]
    is_blocked: bool


class DeadlineItem(BaseModel):
    objective_title: str
    key_result_title: str
    owner: Optional[str]
    deadline: Optional[date]
    progress: float


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    agent: str
    answer: str


class AgentLogOut(BaseModel):
    id: int
    question: str
    routed_agent: str
    response: str
    created_at: datetime

    class Config:
        from_attributes = True
