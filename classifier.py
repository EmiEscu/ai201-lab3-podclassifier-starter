import json
import os
from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_LABELS, DATA_PATH, TRAIN_FILE, LABELS_FILE

_client = Groq(api_key=GROQ_API_KEY)


def load_labeled_examples() -> list[dict]:
    """
    Load the training episodes and merge them with the student's labels.

    Returns a list of dicts, each with:
      - "id"          : episode ID
      - "title"       : episode title
      - "podcast"     : podcast name
      - "description" : episode description
      - "label"       : the label from my_labels.json (may be None if not yet annotated)

    Only returns episodes where the label is a valid, non-null string.
    Episodes with null labels are silently skipped.
    """
    train_path = os.path.join(DATA_PATH, TRAIN_FILE)
    labels_path = os.path.join(DATA_PATH, LABELS_FILE)

    with open(train_path, encoding="utf-8") as f:
        episodes = {ep["id"]: ep for ep in json.load(f)}

    with open(labels_path, encoding="utf-8") as f:
        labels = {entry["id"]: entry["label"] for entry in json.load(f)}

    labeled = []
    for ep_id, ep in episodes.items():
        label = labels.get(ep_id)
        if label in VALID_LABELS:
            labeled.append({**ep, "label": label})

    return labeled


def build_few_shot_prompt(labeled_examples: list[dict], description: str) -> str:
    lines = []

    lines.append(
        "You are classifying podcast episodes by their format. "
        "Classify the episode into exactly one of these four labels:\n"
        "\n"
        "- interview: a conversation between a host and one or more guests\n"
        "- solo: a single host speaking from memory, experience, or opinion — no guests,\n"
        "  no assembled external sources\n"
        "- panel: multiple guests with roughly equal speaking time, often debating or\n"
        "  discussing a topic together\n"
        "- narrative: a story assembled from external sources — interviews, archival\n"
        "  audio, reporting — with a clear narrative arc\n"
        "\n"
        "Return only the label and your reasoning. Do not explain the taxonomy."
    )
    lines.append("")

    if not labeled_examples:
        lines.append("No labeled examples are available. Use only the taxonomy definitions above.")
    else:
        for example in labeled_examples:
            lines.append("---")
            lines.append(f"Title: {example['title']}")
            lines.append(f"Description: {example['description']}")
            lines.append(f"Label: {example['label']}")
            lines.append("")

    lines.append("---")
    lines.append(f"Description: {description}")
    lines.append("Label: ?")
    lines.append("")
    lines.append("Classify the episode above. Return your answer in the format below:")
    lines.append('{"label": "interview", "reasoning": "brief explanation of why"}')

    return "\n".join(lines)


def classify_episode(description: str, labeled_examples: list[dict]) -> dict:
    try:
        # Step 1 — build prompt
        prompt = build_few_shot_prompt(labeled_examples, description)

        # Step 2 — send to LLM
        response = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        raw_text = response.choices[0].message.content

        # Step 3 — strip markdown fences, parse JSON
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
        parsed = json.loads(cleaned)
        reasoning = parsed["reasoning"]

        # Step 4 — normalize and validate label
        label = parsed["label"].strip().lower()
        if label not in VALID_LABELS:
            print(f"[classify_episode] unexpected label — raw response: {raw_text}")
            label = "unknown"

        return {"label": label, "reasoning": reasoning}

    except Exception as e:
        print(f"[classify_episode] error: {e}")
        return {"label": "unknown", "reasoning": f"error: {e}"}
