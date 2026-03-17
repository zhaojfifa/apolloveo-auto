from typing import Optional


class SubtitlesError(Exception):
    """Raised when Step2 (subtitles pipeline) fails in a recoverable way."""

    def __init__(self, message: str, *, cause: Optional[BaseException] = None):
        super().__init__(message)
        self.message = message
        self.cause = cause


class StepError(Exception):
    """Structured error for pipeline step failures.

    Attributes:
        step: Pipeline step name (parse/subtitles/dub/compose/publish).
        category: Error category — transient (retry-able), permanent, or user_input.
        provider: Provider that caused the error, if applicable.
        retryable: Whether the operation can be retried.
    """

    def __init__(
        self,
        message: str,
        *,
        step: str,
        category: str = "permanent",
        provider: Optional[str] = None,
        retryable: bool = False,
        cause: Optional[BaseException] = None,
    ):
        super().__init__(message)
        self.message = message
        self.step = step
        self.category = category  # transient | permanent | user_input
        self.provider = provider
        self.retryable = retryable
        self.cause = cause

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "category": self.category,
            "provider": self.provider,
            "retryable": self.retryable,
            "message": self.message,
        }
