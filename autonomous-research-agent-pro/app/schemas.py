from pydantic import BaseModel, Field
from typing import List

class ResearchRequest(BaseModel):
    query: str = Field(min_length=5, max_length=1000)
    export_pdf: bool = False

class SourceReference(BaseModel):
    title: str
    url: str
    why_relevant: str

class ResearchReport(BaseModel):
    key_points: List[str]
    important_findings: List[str]
    actionable_insights: List[str]
    sources: List[SourceReference]

class ResearchResponse(BaseModel):
    query: str
    search_queries: List[str]
    report: ResearchReport
    markdown_path: str
    pdf_path: str | None = None
