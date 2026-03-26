from __future__ import annotations

SYSTEM_PROMPT = """You are a technical news analyst. Given a batch of articles, produce a structured digest.

For each article:
- Write 3-5 concise bullet points capturing the key facts
- Assign a topic category (e.g. "AI & Machine Learning", "Security", "Web Development", "Cloud", "Open Source")
- Provide one actionable insight: either something the reader can Apply immediately, or a Read More recommendation

Return your response by calling the store_digest tool with the structured data.

Example article input:
{"id": "abc123", "title": "OpenAI releases GPT-5", "snippet": "OpenAI has released GPT-5 with improved reasoning..."}

Example tool call output for that article:
{"id": "abc123", "bullets": ["GPT-5 shows 40% improvement on reasoning benchmarks.", "Available via API starting today.", "New pricing tier introduced for enterprise."], "topic": "AI & Machine Learning", "actionable_insight": {"type": "Apply", "text": "Test GPT-5 on your current prompts to see if reasoning quality improves for your use case."}}
"""

STORE_DIGEST_TOOL: dict = {
    "name": "store_digest",
    "description": "Store the structured digest for a batch of articles.",
    "input_schema": {
        "type": "object",
        "properties": {
            "articles": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "bullets", "topic", "actionable_insight"],
                    "properties": {
                        "id": {"type": "string"},
                        "bullets": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 3,
                            "maxItems": 5,
                        },
                        "topic": {"type": "string"},
                        "actionable_insight": {
                            "type": "object",
                            "required": ["type", "text"],
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["Apply", "Read More"],
                                },
                                "text": {"type": "string"},
                            },
                        },
                    },
                },
            }
        },
        "required": ["articles"],
    },
}
