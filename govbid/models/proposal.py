"""Data models for Grounded Proposal Prose Generation and Compliance Drafts."""

from typing import List
from pydantic import BaseModel, Field


class ProposalSection(BaseModel):
    """An individual structured section of a government proposal response."""
    section_id: str = Field(..., description="Unique section identifier, e.g. SEC-01-EXEC-SUMMARY")
    title: str = Field(..., description="Formal section heading")
    narrative: str = Field(..., description="Synthesized proposal prose in Markdown")
    citations: List[str] = Field(default_factory=list, description="Verified past performance record IDs and statutory citations")
    word_count: int = Field(default=0, description="Total word count of synthesized narrative")


class ProposalDraft(BaseModel):
    """Complete synthesized government contract proposal response document."""
    solicitation_number: str = Field(..., description="Target RFP PIN or solicitation number")
    solicitation_title: str = Field(..., description="Official solicitation title")
    issuing_agency: str = Field(..., description="Contracting authority or department")
    vendor_name: str = Field(..., description="Prime contractor legal name")
    sections: List[ProposalSection] = Field(default_factory=list, description="Ordered proposal response sections")
    groundedness_score: float = Field(..., description="RAG Triad empirical groundedness score (0.0 - 1.0)")
    total_words: int = Field(..., description="Total word count across all sections")
    total_citations: int = Field(..., description="Total number of empirical citations embedded")
    is_submission_ready: bool = Field(..., description="True if groundedness >= 0.80 and all mandatory compliance sections present")
    generated_at: str = Field(..., description="ISO 8601 generation timestamp")
    full_markdown: str = Field(..., description="Complete combined Markdown proposal document")
