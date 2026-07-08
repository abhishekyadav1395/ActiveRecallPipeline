from __future__ import annotations

import time

from active_recall_pipeline.config import (
    Provider,
    PROVIDER_PRICING,
    MAX_RETRIES_PER_PROVIDER,
    BACKOFF_BASE_SECONDS,
    BACKOFF_CAP_SECONDS,
    CACHE_WARM_THRESHOLD_SECONDS,
    PipelineConfig,
)
from active_recall_pipeline.providers.anthropic import AnthropicProvider
from active_recall_pipeline.providers.deepseek import DeepSeekProvider
from active_recall_pipeline.providers.gemini import GeminiProvider
from active_recall_pipeline.providers.base import (
    BaseProvider,
    LLMBusyError,
    LLMFatalError,
)


PROVIDER_MODELS = {
    Provider.ANTHROPIC_HAIKU: "claude-haiku-4-5-20251001",
    Provider.ANTHROPIC_SONNET: "claude-sonnet-4-5",
    Provider.GEMINI_FLASH: "gemini-2.5-flash-preview-05-20",
    Provider.GEMINI_PRO: "gemini-2.5-pro-preview-05-06",
    Provider.DEEPSEEK_V4:     "deepseek-v4-flash",
    Provider.DEEPSEEK_V4_PRO: "deepseek-v4-pro",
    Provider.DEEPSEEK_R1:     "deepseek-reasoner",
}

PROVIDER_CLASSES = {
    Provider.ANTHROPIC_HAIKU: AnthropicProvider,
    Provider.ANTHROPIC_SONNET: AnthropicProvider,
    Provider.GEMINI_FLASH: GeminiProvider,
    Provider.GEMINI_PRO: GeminiProvider,
    Provider.DEEPSEEK_V4:     DeepSeekProvider,
    Provider.DEEPSEEK_V4_PRO: DeepSeekProvider,
    Provider.DEEPSEEK_R1:     DeepSeekProvider,
}


class ProviderRouter:

    def __init__(self, cfg: PipelineConfig, stage: str, db_logger=None):
        self.cfg = cfg
        self.stage = stage
        self.tier = cfg.get_stage_tier(stage)
        self.waterfall = cfg.get_waterfall(self.tier)
        self.db_logger = db_logger
        self._last_call_time: float = 0.0
        self._providers: dict[Provider, BaseProvider] = {}

    def _get_provider(self, provider_key: Provider) -> BaseProvider:
        """Lazy initialize provider on first use."""
        if provider_key not in self._providers:
            model = PROVIDER_MODELS[provider_key]
            cls = PROVIDER_CLASSES[provider_key]

            if provider_key in (Provider.ANTHROPIC_HAIKU,
                                Provider.ANTHROPIC_SONNET):
                p = cls(model=model, api_key=self.cfg.api_key)
            elif provider_key in (Provider.GEMINI_FLASH,
                                  Provider.GEMINI_PRO):
                p = cls(model=model, api_key=self.cfg.gemini_api_key)
            else:
                p = cls(model=model, api_key=self.cfg.deepseek_api_key)

            p.initialize()
            self._providers[provider_key] = p

        return self._providers[provider_key]

    def _warm_cache_if_needed(self, provider: BaseProvider,
                               system_prompt: str) -> None:
        """Reset cache TTL if approaching expiry."""
        elapsed = time.time() - self._last_call_time
        if elapsed > CACHE_WARM_THRESHOLD_SECONDS:
            provider.warm_cache(system_prompt)

    def _calculate_cost(self, provider_name: str,
                         input_tokens: int,
                         output_tokens: int) -> float:
        """Calculate cost in USD from token counts."""
        pricing = PROVIDER_PRICING.get(provider_name,
                                        {"input": 0, "output": 0})
        return (input_tokens * pricing["input"] / 1_000_000 +
                output_tokens * pricing["output"] / 1_000_000)

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 64000,
        thinking_budget: int = 0,
        chapter_id: int | None = None,
    ) -> str:
        """Call providers in waterfall order.
        Retry each with exponential backoff before switching.
        Log every attempt to SQLite if db_logger provided.
        Return content string on success.
        Raise LLMFatalError if all providers exhausted."""

        for provider_key in self.waterfall:
            try:
                provider = self._get_provider(provider_key)
            except LLMFatalError:
                if self.db_logger and chapter_id:
                    self.db_logger.log_api_call(
                        chapter_id=chapter_id,
                        stage=self.stage,
                        provider=provider_key.value,
                        model=PROVIDER_MODELS[provider_key],
                        tier=self.tier,
                        input_tokens=0,
                        output_tokens=0,
                        cost_usd=0.0,
                        duration_seconds=0.0,
                        success=False,
                        error_type="fatal",
                    )
                continue
            self._warm_cache_if_needed(provider, system_prompt)

            retries = 0
            while retries <= MAX_RETRIES_PER_PROVIDER:
                start = time.time()
                try:
                    response = provider.generate_content(
                        system_prompt, user_prompt,
                        max_tokens, thinking_budget
                    )
                    duration = time.time() - start
                    self._last_call_time = time.time()

                    cost = self._calculate_cost(
                        response.provider_name,
                        response.input_tokens,
                        response.output_tokens
                    )

                    if self.db_logger and chapter_id:
                        self.db_logger.log_api_call(
                            chapter_id=chapter_id,
                            stage=self.stage,
                            provider=response.provider_name,
                            model=response.model_name,
                            tier=self.tier,
                            input_tokens=response.input_tokens,
                            output_tokens=response.output_tokens,
                            cost_usd=cost,
                            duration_seconds=duration,
                            success=True,
                        )
                        self.db_logger.update_cost_ledger(
                            chapter_id=chapter_id,
                            provider=response.provider_name,
                            tier=self.tier,
                            input_tokens=response.input_tokens,
                            output_tokens=response.output_tokens,
                            cost_usd=cost,
                        )

                    return response.content

                except LLMBusyError as e:
                    duration = time.time() - start
                    if self.db_logger and chapter_id:
                        self.db_logger.log_api_call(
                            chapter_id=chapter_id,
                            stage=self.stage,
                            provider=provider_key.value,
                            model=PROVIDER_MODELS[provider_key],
                            tier=self.tier,
                            input_tokens=0,
                            output_tokens=0,
                            cost_usd=0.0,
                            duration_seconds=duration,
                            success=False,
                            error_type="busy",
                        )

                    retries += 1
                    if retries > MAX_RETRIES_PER_PROVIDER:
                        break

                    wait = min(BACKOFF_CAP_SECONDS,
                               BACKOFF_BASE_SECONDS ** retries)
                    time.sleep(wait)

                except LLMFatalError:
                    if self.db_logger and chapter_id:
                        self.db_logger.log_api_call(
                            chapter_id=chapter_id,
                            stage=self.stage,
                            provider=provider_key.value,
                            model=PROVIDER_MODELS[provider_key],
                            tier=self.tier,
                            input_tokens=0,
                            output_tokens=0,
                            cost_usd=0.0,
                            duration_seconds=time.time() - start,
                            success=False,
                            error_type="fatal",
                        )
                    break

        raise LLMFatalError(
            f"All providers exhausted for stage {self.stage} tier {self.tier}"
        )

    def count_tokens(self, system_prompt: str,
                      user_prompt: str) -> int:
        """Count tokens using first available provider."""
        for provider_key in self.waterfall:
            try:
                provider = self._get_provider(provider_key)
                return provider.count_tokens(system_prompt, user_prompt)
            except Exception:
                continue
        return (len(system_prompt) + len(user_prompt)) // 4
