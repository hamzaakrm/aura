"""
AURA Business Engine (Phase 6)
Content generation and lightweight business tools: product descriptions,
SEO keyword ideas, email drafts, and general content writing.
Everything here runs through your local model -- nothing is sent anywhere.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Config"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Brain"))
import settings                   # noqa: E402
from chat_engine import ask_aura  # noqa: E402


def write_product_description(product_name: str, details: str) -> str:
    prompt = [
        {"role": "system", "content": (
            "You are a skilled e-commerce copywriter. Write a compelling, "
            "conversion-focused product description. Structure it with a "
            "short hook line, 3-5 bullet points on key features/benefits, "
            "and a short closing line. Only use details actually given -- "
            "do not invent specifications or claims that weren't provided."
        )},
        {"role": "user", "content": f"Product: {product_name}\nDetails: {details}"},
    ]
    return ask_aura(prompt)


def write_seo_keywords(topic: str) -> str:
    prompt = [
        {"role": "system", "content": (
            "You are an SEO strategist. Given a topic, produce: "
            "1) 8-10 relevant keyword phrases a shopper might search, "
            "2) 3 suggested page title options, "
            "3) a 1-2 sentence meta description. "
            "Format clearly with headers for each section."
        )},
        {"role": "user", "content": f"Topic: {topic}"},
    ]
    return ask_aura(prompt)


def draft_email(purpose: str, key_points: str) -> str:
    prompt = [
        {"role": "system", "content": (
            "Draft a clear, professional email based on the purpose and "
            "key points given. Include a subject line, greeting, body, "
            "and a sign-off placeholder. Friendly but businesslike tone."
        )},
        {"role": "user", "content": f"Purpose: {purpose}\nKey points: {key_points}"},
    ]
    return ask_aura(prompt)


def write_content(content_type: str, topic: str) -> str:
    prompt = [
        {"role": "system", "content": (
            f"Write a {content_type} about the given topic. Match the "
            f"typical style, tone, and length of a {content_type}. "
            "Make it engaging and well-structured."
        )},
        {"role": "user", "content": f"Topic: {topic}"},
    ]
    return ask_aura(prompt)