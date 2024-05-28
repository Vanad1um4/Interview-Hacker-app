import asyncio
import time

from openai import OpenAI
from env import OPENAI_API_KEY, MODEL, SYSTEM_PROMPT
from utils import write_to_file

client = OpenAI(api_key=OPENAI_API_KEY)


async def get_openai_response(prompt, recognized_text):
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': f'{prompt} \n\n {recognized_text}'},
    ]

    try:
        stream = await asyncio.to_thread(
            client.chat.completions.create,
            model=MODEL,
            messages=messages,
            stream=True
        )
    except Exception as e:
        write_to_file('errors.log', f'{int(time.time())}: Ошибка генерации: {str(e)}', add=True)
        return

    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content
