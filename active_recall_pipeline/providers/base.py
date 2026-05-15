from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    input_tokens: int
    output_tokens: int
    provider_name: str
    model_name: str


class LLMBusyError(Exception):
    """Transient error — retry or switch provider.
    Raised for: 429 rate limit, 503 overloaded,
    connection timeout, network errors."""
    pass


class LLMFatalError(Exception):
    """Permanent error — do not retry this provider.
    Raised for: 400 bad request, 401 auth failure,
    404 model not found, 500 internal error."""
    pass


class BaseProvider(ABC):

    @abstractmethod
    def initialize(self) -> None:
        """Load API keys and SDK clients. Called once."""
        pass

    @abstractmethod
    def generate_content(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 64000,
        thinking_budget: int = 0,
    ) -> LLMResponse:
        """Generate content. Return normalized LLMResponse.
        Raise LLMBusyError for transient failures.
        Raise LLMFatalError for permanent failures."""
        pass

    @abstractmethod
    def count_tokens(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> int:
        """Count tokens. Used by build_batches().
        Must not raise LLMBusyError — token counting
        should always succeed or return an estimate."""
        pass

    @abstractmethod
    def warm_cache(self, system_prompt: str) -> None:
        """Send a cheap request to reset cache TTL.
        Use count_tokens internally. Silent on failure."""
        pass
