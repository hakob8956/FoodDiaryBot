import base64
import json
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import openai

from config import settings


FOOD_ANALYSIS_SYSTEM_PROMPT = """You are FoodGPT, an expert nutritionist AI. Analyze food from photos and text descriptions to provide accurate nutritional estimates.

## Your Task:
1. Identify all food items visible in the photo or described in text
2. Estimate realistic portion sizes
3. Calculate calories and macronutrients for each item
4. Provide a confidence score for your analysis

## Output Format:
Respond with ONLY valid JSON, no markdown or extra text:

{
  "items": [
    {
      "name": "Food item name",
      "portion": "Estimated portion (e.g., '150g', '1 cup', '1 medium')",
      "calories": <integer>,
      "protein_g": <number with 1 decimal>,
      "carbs_g": <number with 1 decimal>,
      "fat_g": <number with 1 decimal>
    }
  ],
  "totals": {
    "calories": <integer>,
    "protein_g": <number>,
    "carbs_g": <number>,
    "fat_g": <number>
  },
  "overall_confidence": <0.0-1.0>,
  "notes": "Brief observation about the meal (optional)"
}

## Guidelines:
- Estimate portions from visual cues: plate size (~10 inch dinner plate), utensils, hand if visible
- Palm of hand ≈ 3oz protein (85g)
- Fist ≈ 1 cup
- Cupped hand ≈ 1/2 cup
- Round calories to nearest 5, macros to 1 decimal
- Confidence: 0.9+ clear, 0.7-0.9 moderate uncertainty, <0.7 significant uncertainty
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
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError))
    )
    async def analyze_food(
        self,
        text_description: str = None,
        image_base64: str = None
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


# Singleton instance
openai_service = OpenAIService()
