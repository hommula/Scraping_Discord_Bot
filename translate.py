import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

def translate_text(text, target_language="English"):
    try:
        translated_text = client.chat.completions.create(
            model = "gpt-4o-mini",
            messages = [
                {"role": "system", "content": f"You are a translator who is going to translate auction item description from a Japanese website. Translate the following text to {target_language}. Only provide the translation, no explanations."},
                {"role": "user", "content": text}
            ],
            temperature = 0.2
        )
        response = client.chat.completions.create(
            model = "gpt-4o-mini",
            messages = [
                {"role": "system", "content": f"You are a agent who is going to summarize given text into a short and clear paragraph in {target_language}. Strictly do not use bullet point, summarize every into a very short paragraph that does not exceed 1500 characters. Strictly ignore all content relating to shipping and payment, do not include them in your response."},
                {"role": "user", "content": translated_text.choices[0].message.content}
            ],
            temperature = 0.6
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"Translation error: {str(e)}"
