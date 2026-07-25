from __future__ import annotations

from abc import ABC, abstractmethod

from prosebench.document import NumberedDocument
from prosebench.models import AssessmentContext, AssessmentResult, ProviderAssessmentDraft, ProviderRevisionDraft
from prosebench.rubric import RubricProfile


class ProseProvider(ABC):
    name: str
    model: str

    @abstractmethod
    def assess(
        self,
        document: NumberedDocument,
        rubric: RubricProfile,
        context: AssessmentContext,
    ) -> ProviderAssessmentDraft:
        raise NotImplementedError

    @abstractmethod
    def revise(
        self,
        document: NumberedDocument,
        rubric: RubricProfile,
        assessment: AssessmentResult,
        focus: list[str],
        mode: str,
        fact_lock: str,
    ) -> ProviderRevisionDraft:
        raise NotImplementedError
