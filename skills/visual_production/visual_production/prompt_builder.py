"""Prompt builder — hydrate nano-prompts with context and assemble system prompts.

Supports both direct string formatting and LLM-call-style prompt dicts
(messages list with system + user roles).
"""
from __future__ import annotations

from typing import Optional

from .nano_prompts import (
    MARKDOWN_POLISH,
    EXTRACT_SOURCES,
    SUMMARY_BLURB,
    INFOGRAPHIC_LABEL,
    INFOGRAPHIC_IMAGE,
)
from .schemas import MagazineConfig, ProductType, NanoBananaRoute


def build_prompt(
    template: str,
    /,
    **kwargs,
) -> str:
    """Hydrate a nano-prompt template with keyword arguments.

    Parameters
    ----------
    template : str
        The template string with {placeholders}.
    **kwargs
        Values to substitute.

    Returns
    -------
    str
        Hydrated prompt.

    Raises
    ------
    KeyError
        If a placeholder in the template is missing from kwargs.
    """
    return template.format(**kwargs)


def build_messages(
    template: str,
    system_context: str = "",
    /,
    **kwargs,
) -> list[dict[str, str]]:
    """Hydrate a template and wrap it in an LLM messages list.

    Parameters
    ----------
    template : str
        Nano-prompt template.
    system_context : str
        Optional system-level instruction prepended.
    **kwargs
        Template variables.

    Returns
    -------
    list[dict]
        ``[{"role": "system", "content": ...}, {"role": "user", "content": ...}]``
    """
    user_prompt = build_prompt(template, **kwargs)
    messages = []
    if system_context:
        messages.append({"role": "system", "content": system_context})
    messages.append({"role": "user", "content": user_prompt})
    return messages


def build_infographic_prompt(
    raw_text: str,
    route: NanoBananaRoute = NanoBananaRoute.LOGIC_FLOW,
    extra_context: str = "",
) -> str:
    """Build a prompt suitable for image generation via OpenRouter.

    The prompt includes layout structure, hierarchy, and infographic
    styling constraints — no Mermaid, tables, or raw code.

    Parameters
    ----------
    raw_text : str
        The analysis text to visualise.
    route : NanoBananaRoute
        The NanoBanana routing label (logic_flow, flow_chain, map_plate, etc.).
    extra_context : str
        Additional context (e.g. "Focus on the Strait of Hormuz chokepoint.").

    Returns
    -------
    str
        Prompt string ready for ``--prompt``.
    """
    return build_prompt(
        INFOGRAPHIC_IMAGE,
        route=route.value.replace("_", " ").title(),
        raw_text=raw_text,
        extra_context=extra_context or "",
    )


def system_context_for_product(
    product: ProductType,
    config: MagazineConfig,
) -> str:
    """Build a system-level context string for the given product type."""
    contexts = {
        ProductType.MAGAZINE: (
            f"You are a senior editor for {config.title}. "
            f"Classification: {config.classification.value}. "
            f"Issue: {config.issue}. "
            "Format output as polished magazine-ready markdown."
        ),
        ProductType.BRIEF: (
            "You are an intelligence briefer preparing a concise executive brief. "
            "Be direct, factual, and prioritise actionable information."
        ),
        ProductType.INFOGRAPHIC: (
            "You are a data journalist preparing content for infographic layout. "
            "Focus on key numbers, relationships, and visualisable insights."
        ),
        ProductType.SLIDE: (
            "You are a briefing officer preparing slide content. "
            "Use short bullets, minimal text, one idea per slide."
        ),
        ProductType.REPORT: (
            "You are an intelligence analyst formatting a formal written report. "
            "Maintain structured sections with clear analytic judgements."
        ),
    }
    return contexts.get(product, contexts[ProductType.MAGAZINE])
