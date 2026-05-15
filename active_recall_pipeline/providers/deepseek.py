from __future__ import annotations

from active_recall_pipeline.providers.base import (
    BaseProvider,
    LLMBusyError,
    LLMFatalError,
    LLMResponse,
)


class DeepSeekProvider(BaseProvider):

    def __init__(self, model: str, api_key: str):
        self.model = model
        self.api_key = api_key
        self._client = None

    def initialize(self) -> None:
        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )
        except ImportError:
            raise LLMFatalError(
                "openai package not installed. "
                "Install with: pip install openai"
            )
        except Exception as e:
            raise LLMFatalError(f"Failed to initialize DeepSeek client: {e}")

    def generate_content(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 64000,
        thinking_budget: int = 0,
    ) -> LLMResponse:
        try:
            from openai import (
                RateLimitError,
                APIStatusError,
                APITimeoutError,
                APIConnectionError,
                AuthenticationError,
                BadRequestError,
            )
        except ImportError:
            raise LLMFatalError("openai package not available")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                stream=False,
            )

            text = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

            provider_name = (
                "deepseek_v3" if "chat" in self.model
                else "deepseek_r1"
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
        return (len(system_prompt) + len(user_prompt)) // 4

    def warm_cache(self, system_prompt: str) -> None:
        pass
