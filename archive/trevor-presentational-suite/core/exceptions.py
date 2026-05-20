"""TPS Exceptions — suite-specific error types."""
from __future__ import annotations


class TPSError(Exception):
    """Base exception for all TPS errors."""


class IngestError(TPSError):
    """Failed to parse a TREVOR document."""


class PlanValidationError(TPSError):
    """Presentation plan failed validation (e.g. image-gen routed to map)."""


class ApprovalRequiredError(TPSError):
    """Execution attempted without required cost approval."""


class BudgetExceededError(TPSError):
    """TPS generation would exceed TREVOR's budget caps."""


class GeneratorError(TPSError):
    """A generator failed to produce output."""


class GeneratorUnavailableError(GeneratorError):
    """A generator's dependencies are not available."""


class ProviderError(TPSError):
    """An external provider API call failed."""


class CacheError(TPSError):
    """Cache read/write failure."""


class StalePricingWarning(UserWarning):
    """Provider pricing data is older than 30 days."""
