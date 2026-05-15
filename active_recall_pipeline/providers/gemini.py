from __future__ import annotations

from active_recall_pipeline.providers.base import (
    BaseProvider,
    LLMBusyError,
    LLMFatalError,
    LLMResponse,
)


class GeminiProvider(BaseProvider):

    def __init__(self, model: str, api_key: str):
        self.model = model
        self.api_key = api_key
        self._client = None

    def initialize(self) -> None:
        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        except ImportError:
            raise LLMFatalError(
                "google-genai package not installed. "
                "Install with: pip install google-genai"
            )
        except Exception as e:
            raise LLMFatalError(f"Failed to initialize Gemini client: {e}")

    def generate_content(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 64000,
        thinking_budget: int = 0,
    ) -> LLMResponse:
        try:
            from google.genai import types
            from google.api_core.exceptions import (
                ResourceExhausted,
                ServiceUnavailable,
                DeadlineExceeded,
                Unauthenticated,
                InvalidArgument,
            )
        except ImportError:
            raise LLMFatalError("google-genai package not available")

        try:
            config = types.CountTokensConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_tokens,
            )

            if thinking_budget > 0:
                config.thinking_config = types.ThinkingConfig(
                    thinking_budget=thinking_budget
                )

            response = self._client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=config,
            )

            text = response.text
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count

            provider_name = (
                "gemini_flash" if "flash" in self.model
                else "gemini_pro"
            )

            return LLMResponse(
                content=text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                provider_name=provider_name,
                model_name=self.model,
            )

        except ResourceExhausted as e:
            raise LLMBusyError(f"Resource exhausted: {e}")
        except ServiceUnavailable as e:
            raise LLMBusyError(f"Service unavailable: {e}")
        except DeadlineExceeded as e:
            raise LLMBusyError(f"Request timed out: {e}")
        except Unauthenticated as e:
            raise LLMFatalError(f"Authentication failed: {e}")
        except InvalidArgument as e:
            raise LLMFatalError(f"Invalid argument: {e}")
        except Exception as e:
            raise LLMFatalError(f"Unexpected error: {e}")

    def count_tokens(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> int:
        try:
            from google.genai import types

            response = self._client.models.count_tokens(
                model=self.model,
                contents=user_prompt,
                config=types.CountTokensConfig(
                    system_instruction=system_prompt
                )
            )
            return response.total_tokens
        except Exception:
            return (len(system_prompt) + len(user_prompt)) // 4

    def warm_cache(self, system_prompt: str) -> None:
        try:
            self.count_tokens(system_prompt, "warm")
        except Exception:
            pass
