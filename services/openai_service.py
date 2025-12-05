"""
OpenAI GPT-4o Vision service.

Handles food analysis using GPT-4o vision capabilities.
"""

import base64
import json
from typing import Optional

from openai import AsyncOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import openai

from config import settings
from constants import CONFIDENCE_HIGH, CONFIDENCE_WARNING_THRESHOLD


FOOD_ANALYSIS_SYSTEM_PROMPT = f"""You are FoodGPT, an expert nutritionist AI. Analyze food from photos and text descriptions to provide accurate nutritional estimates.

## Your Task:
1. Identify all food items visible in the photo or described in text
2. Estimate realistic portion sizes
3. Calculate calories and macronutrients for each item
4. Provide a confidence score for your analysis

## Output Format:
Respond with ONLY valid JSON, no markdown or extra text:

{{
  "items": [
    {{
      "name": "Food item name",
      "portion": "Estimated portion (e.g., '150g', '1 cup', '1 medium')",
      "calories": <integer>,
      "protein_g": <number with 1 decimal>,
      "carbs_g": <number with 1 decimal>,
      "fat_g": <number with 1 decimal>
    }}
  ],
  "totals": {{
    "calories": <integer>,
    "protein_g": <number>,
    "carbs_g": <number>,
    "fat_g": <number>
  }},
  "overall_confidence": <0.0-1.0>,
  "notes": "Brief observation about the meal (optional)"
}}

## Guidelines:
- Estimate portions from visual cues: plate size (~10 inch dinner plate), utensils, hand if visible
- Palm of hand ≈ 3oz protein (85g)
- Fist ≈ 1 cup
- Cupped hand ≈ 1/2 cup
- Round calories to nearest 5, macros to 1 decimal
- Confidence: {CONFIDENCE_HIGH}+ clear, {CONFIDENCE_WARNING_THRESHOLD}-{CONFIDENCE_HIGH} moderate uncertainty, <{CONFIDENCE_WARNING_THRESHOLD} significant uncertainty
- When uncertain, err toward slightly higher calorie estimates
- Account for cooking methods: fried adds ~50-100 cal per serving
- Consider visible sauces, oils, dressings"""


class OpenAIService:
    """Service for interacting with OpenAI GPT-4o Vision API."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (openai.RateLimitError, openai.APITimeoutError))
    )
    async def analyze_food(
        self,
        text_description: Optional[str] = None,
        image_base64: Optional[str] = None
    ) -> dict:
        """
        Analyze food from image and/or text description.

        Args:
            text_description: Optional text describing the food
            image_base64: Optional base64-encoded image

        Returns:
            Parsed JSON response with food analysis
        """
        messages = [
            {"role": "system", "content": FOOD_ANALYSIS_SYSTEM_PROMPT}
        ]

        # Build user message content
        content = []

        if image_base64:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}",
                    "detail": "high"
                }
            })

        # Build the text prompt
        if image_base64 and text_description:
            prompt = f'Analyze this food image. User description: "{text_description}"'
        elif image_base64:
            prompt = "Analyze this food image and estimate nutritional content."
        else:
            prompt = f'Analyze this food description and provide nutritional estimates: "{text_description}"'

        content.append({"type": "text", "text": prompt})
        messages.append({"role": "user", "content": content})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=settings.openai_max_tokens,
            temperature=settings.openai_temperature
        )

        # Parse the response
        response_text = response.choices[0].message.content.strip()

        # Clean up potential markdown formatting
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        return json.loads(response_text.strip())

    async def encode_image_from_bytes(self, image_bytes: bytes) -> str:
        """Encode image bytes to base64 string."""
        return base64.b64encode(image_bytes).decode("utf-8")

    async def generate_reminder_message(self, food_list: list[str]) -> str:
        """
        Generate a personalized reminder message based on user's food history.

        Args:
            food_list: List of food item names from last 7 days

        Returns:
            AI-generated reminder message
        """
        food_log_text = ", ".join(food_list) if food_list else "Nothing logged"

        system_prompt = """You are a dramatic, emotional, hungry little food-tracking creature.
Your job is to send the user a short reminder message based on the food they logged in the last 7 days.

Tone:
- emotional, cute, needy, very friendly
- like a pet begging its owner gently
- slightly funny but still warm and motivating
- message should feel personal based on the foods they actually logged
- message should be very short and simple enought not overwhelm the user and not poetic

Rules:
- Use only the foods that appear in the last 7 days
- If the user barely logged anything, be extra dramatic and sad
- If the user logged many things, be excited and proud
- Keep message SHORT (1–3 sentences)
- Never guilt-trip aggressively — only playful sadness
- End with a gentle nudge to log today's food"""

        user_prompt = f"""Here is the user's food log from the last 7 days:
{food_log_text}

Generate ONE message."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=150,
            temperature=0.9
        )

        return response.choices[0].message.content.strip()


# Singleton instance
openai_service = OpenAIService()
