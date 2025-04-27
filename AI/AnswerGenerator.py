import aiohttp
import json
import os
from dotenv import load_dotenv

import logging
import logging_config

load_dotenv()
logger = logging.getLogger(__name__)
AI_API_KEY = os.getenv('AI_API_KEY')
PastePromt = os.getenv('PastePromt')


async def ai_answer_generator(users_content):
    logger.info(f'Getting answer for "{users_content}"')
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {AI_API_KEY}",
                    "Content-Type": "application/json",
                },
                data=json.dumps({
                    "model": "deepseek/deepseek-chat-v3-0324:free",
                    "messages": [
                        {
                            "role": "user",
                            "content": f"{PastePromt} {users_content}"
                        }
                    ],
                })
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    answer = data["choices"][0]["message"]["content"]
                    return answer
                else:
                    logger.error(f"Error while getting answer for {users_content}: Status code {response.status}")
                    return "Error while getting answer. Please contact developers."
    except Exception as e:
        logger.error(f"Error while getting answer for {users_content}: {e}")
        return "Error while getting answer. Please contact developers."