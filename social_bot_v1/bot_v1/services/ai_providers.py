"""সব AI-এর API কল এখানে। নতুন AI যোগ করতে শুধু এখানে একটা ফাংশন বসাও।"""
import aiohttp

import config

TIMEOUT = aiohttp.ClientTimeout(total=60)


async def _post(session, url, headers, payload):
    async with session.post(url, headers=headers, json=payload) as r:
        if r.status == 200:
            return await r.json()
        text = (await r.text())[:500]
        raise RuntimeError(f"API {r.status}: {text}")


async def _claude(s, key, prompt):
    data = await _post(s, "https://api.anthropic.com/v1/messages", {
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json",
    }, {"model": config.AI_MODELS["Claude"], "max_tokens": 1000,
        "messages": [{"role": "user", "content": prompt}]})
    return data["content"][0]["text"]


async def _openai_style(s, url, key, model, prompt):
    data = await _post(s, url, {"Authorization": f"Bearer {key}", "content-type": "application/json"},
                       {"model": model, "messages": [{"role": "user", "content": prompt}]})
    return data["choices"][0]["message"]["content"]


async def _gemini(s, key, prompt):
    model = config.AI_MODELS["Gemini"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    data = await _post(s, url, {"x-goog-api-key": key, "content-type": "application/json"},
                       {"contents": [{"parts": [{"text": prompt}]}]})
    return data["candidates"][0]["content"]["parts"][0]["text"]


async def ask(provider, key, prompt):
    try:
        async with aiohttp.ClientSession(timeout=TIMEOUT) as s:
            if provider == "Claude":
                return await _claude(s, key, prompt)
            if provider == "ChatGPT":
                return await _openai_style(s, "https://api.openai.com/v1/chat/completions",
                                           key, config.AI_MODELS["ChatGPT"], prompt)
            if provider == "Grok":
                return await _openai_style(s, "https://api.x.ai/v1/chat/completions",
                                           key, config.AI_MODELS["Grok"], prompt)
            if provider == "Gemini":
                return await _gemini(s, key, prompt)
            return f"⚠️ অজানা provider: {provider}"
    except Exception as e:
        return f"⚠️ {provider} এরর: {e}"
