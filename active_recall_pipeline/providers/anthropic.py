from __future__ import annotations

from active_recall_pipeline.providers.base import (
    BaseProvider,
    LLMBusyError,
    LLMFatalError,
    LLMResponse,
)


class AnthropicProvider(BaseProvider):

    def __init__(self, model: str, api_key: str):
        self.model = model
        self.api_key = api_key
        self._client = None

    def initialize(self) -> None:
        try:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=self.api_key, timeout=600.0)
        except ImportError:
            raise LLMFatalError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )
        except Exception as e:
            raise LLMFatalError(f"Failed to initialize Anthropic client: {e}")

    def generate_content(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 64000,
        thinking_budget: int = 0,
    ) -> LLMResponse:
        try:
            from anthropic import (
                RateLimitError,
                APIStatusError,
                APITimeoutError,
                APIConnectionError,
                AuthenticationError,
                BadRequestError,
            )
        except ImportError:
            raise LLMFatalError("anthropic package not available")

        system = [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"}
            }
        ]

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        if thinking_budget > 0:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": thinking_budget
            }

        try:
            with self._client.messages.stream(**kwargs) as stream:
                text = "".join(stream.text_stream)
                final_message = stream.get_final_message()

            input_tokens = final_message.usage.input_tokens
            output_tokens = final_message.usage.output_tokens

            provider_name = (
                "anthropic_haiku" if "haiku" in self.model
                else "anthropic_sonnet"
            )

            return LLMResponse(
                content=text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                provider_name=provider_name,
                model_name=self.model,
            )

        except RateLimitError as e:
            raise LLMBusyError(f"Rate limited: {e}")
        except APIStatusError as e:
            if e.status_code == 503:
                raise LLMBusyError(f"Service unavailable: {e}")
            elif e.status_code == 401:
                raise LLMFatalError(f"Authentication failed: {e}")
            elif e.status_code == 400:
                raise LLMFatalError(f"Bad request: {e}")
            else:
                raise LLMFatalError(f"API error ({e.status_code}): {e}")
        except APITimeoutError as e:
            raise LLMBusyError(f"Request timed out: {e}")
        except APIConnectionError as e:
            raise LLMBusyError(f"Connection error: {e}")
        except AuthenticationError as e:
            raise LLMFatalError(f"Authentication error: {e}")
        except BadRequestError as e:
            raise LLMFatalError(f"Bad request: {e}")
        except Exception as e:
            raise LLMFatalError(f"Unexpected error: {e}")

    def count_tokens(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> int:
        try:
            response = self._client.messages.count_tokens(
                model=self.model,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.input_tokens
        except Exception:
            return (len(system_prompt) + len(user_prompt)) // 4

    def warm_cache(self, system_prompt: str) -> None:
        try:
            self.count_tokens(system_prompt, "warm")
        except Exception:
            pass
