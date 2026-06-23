# Classifier Spec — Pod Classifier

Complete this spec **before** writing any code for Milestone 2.

Use Plan or Ask mode to think through each blank field. When you're done,
your answers here become the blueprint for `build_few_shot_prompt()` and
`classify_episode()` in `classifier.py`.

---

## build_few_shot_prompt(labeled_examples, description)

### What it does
Constructs a prompt string for the LLM that includes the task instructions,
all labeled training examples, and the new episode description to classify.

### Inputs

| Parameter | Type | Description |
|---|---|---|
| `labeled_examples` | `list[dict]` | Each dict has `"title"`, `"description"`, `"label"` (and others). These are the examples you labeled in Milestone 1. |
| `description` | `str` | The episode description to classify. |

### Output

| Return value | Type | Description |
|---|---|---|
| prompt | `str` | A complete prompt string ready to send to the LLM. |

---

### Spec fields — fill these in before writing code

**Task instruction (what should the LLM know about the task?):**

```
You are classifying podcast episodes by their format. Classify the episode
into exactly one of these four labels:

- interview: a conversation between a host and one or more guests
- solo: a single host speaking from memory, experience, or opinion — no guests,
  no assembled external sources
- panel: multiple guests with roughly equal speaking time, often debating or
  discussing a topic together
- narrative: a story assembled from external sources — interviews, archival
  audio, reporting — with a clear narrative arc

Return only the label and your reasoning. Do not explain the taxonomy.
```

---

**How should labeled examples be formatted in the prompt?**

```
Each example should include the episode title, a brief excerpt or the full
description, and the correct label. Separate examples with a blank line or
a delimiter like "---". Include all fields that help the model see why the
label was applied — title and description are both useful; other fields
(like episode ID) are not needed.
```

---

**Example block sketch (write one concrete example):**

```
Title: Dr. Priya Nair on the Science of Sleep Deprivation
Description: Dr. Priya Nair has spent fifteen years studying what happens to the brain when it doesn't sleep. In this episode, we talk through her landmark 2019 study on cumulative sleep debt, what the research says about weekend recovery sleep (spoiler: it doesn't work the way you think), and why she believes the eight-hour standard is more cultural myth than biological fact. She also shares what changed in her own sleep habits after spending a decade measuring everyone else's. If you've ever felt fine on five hours, this conversation will make you rethink that confidence.
Label: interview
```

---

**How should the new episode (to be classified) be presented?**

```
Present it in the same format as the labeled examples, but omit the Label
line and replace it with an instruction to classify. For example:

Title: Dr. Priya Nair on the Science of Sleep Deprivation
Description: Dr. Priya Nair has spent fifteen years studying what happens to the brain when it doesn't sleep. In this episode, we talk through her landmark 2019 study on cumulative sleep debt, what the research says about weekend recovery sleep (spoiler: it doesn't work the way you think), and why she believes the eight-hour standard is more cultural myth than biological fact. She also shares what changed in her own sleep habits after spending a decade measuring everyone else's. If you've ever felt fine on five hours, this conversation will make you rethink that confidence.
Label: ?

Then add a line like: "Classify the episode above. Return your answer in
the format below:" followed by the output format you chose.
```

---

**What output format should you request from the LLM?**

```
Request a single JSON object on one line (not JSONL — this is one response per
call, not a stream of records):

{"label": "interview", "reasoning": "The description mentions a named guest and
uses 'we talk through', signaling a host-guest conversation."}

Tradeoffs:
- JSON: most reliable to parse with json.loads(); fails clearly when malformed;
  matches the dict the function must return. Downside: LLMs sometimes wrap output
  in markdown fences (```json ... ```) — strip those before parsing.
- "Label: X / Reasoning: Y": easy to write but fragile — if the model varies
  punctuation or adds a newline, the split breaks.
- Single label only: trivially parseable but loses reasoning, which the return
  dict requires.

JSON wins because it maps directly onto the {"label": ..., "reasoning": ...}
return value and json.loads() handles validation for free.
```

---

**Edge cases to handle in the prompt:**

```
1. labeled_examples is empty: add a guard before building the examples block.
   If the list is empty, include a note in the prompt:
   "No labeled examples are available. Use only the taxonomy definitions above."
   This prevents the model from seeing a blank section and hallucinating a pattern.

2. Description is very short (e.g., under ~20 words): include all available text
   unchanged — do not truncate. Add no special instruction; the model should
   classify on limited signal and return low-confidence reasoning. The caller
   (classify_episode) handles the "unknown" fallback if the output is unparseable.

3. Description contains special characters or newlines: no special handling needed
   in the prompt itself — just ensure the description is inserted as-is and the
   "---" delimiter between examples is on its own line so it remains unambiguous.
```


---

## classify_episode(description, labeled_examples)

### What it does
Classifies a single podcast episode description using the few-shot LLM classifier.
Returns a dict with a label and reasoning.

### Inputs

| Parameter | Type | Description |
|---|---|---|
| `description` | `str` | The episode description to classify. |
| `labeled_examples` | `list[dict]` | Labeled training examples from `load_labeled_examples()`. |

### Output

| Return value | Type | Description |
|---|---|---|
| result | `dict` | Must have keys `"label"` and `"reasoning"`. `"label"` must be one of `VALID_LABELS` or `"unknown"`. |

---

### Spec fields — fill these in before writing code

**Step 1 — Build the prompt:**

```
Call build_few_shot_prompt(labeled_examples, description) and store the
returned string in a variable (e.g., prompt). Pass through both arguments
exactly as received — no modification needed before calling.
```

---

**Step 2 — Send to the LLM:**

```
Call _client.chat.completions.create() with:
  - model: the model name from config (LLM_MODEL)
  - messages: a list with one dict — {"role": "user", "content": prompt}
    (system-design.md shows an optional system message too — either shape works)
  - max_tokens: a reasonable limit (e.g., 200–300) to keep responses concise

Extract the response text from:
  response.choices[0].message.content
```

---

**Step 3 — Parse the response:**

```
The output format is JSON, so parse with json.loads() — do not split strings.

Steps:
1. Strip leading/trailing whitespace from the raw response text.
2. Strip markdown fences if present: remove a leading ```json or ``` and a
   trailing ```. The model adds these even when not asked.
3. Call json.loads() on the cleaned string.
4. Extract parsed["label"] and parsed["reasoning"].

If json.loads() raises a JSONDecodeError, catch it in Step 5 and return the
fallback dict — do not try to salvage a malformed response with string ops.
```

---

**Step 4 — Validate the label:**

```
After parsing, normalize and validate the label:
1. Call .strip().lower() on parsed["label"].
2. Check if the result is in VALID_LABELS.
3. If yes, use it. If no, set label = "unknown".
4. Log the raw response so the bad output is visible for debugging:
     print(f"[classify_episode] unexpected label — raw response: {raw_text}")
   This makes it possible to diagnose whether the model is drifting in format
   or using a synonym (e.g. "narrated" instead of "narrative").
```
---

**Step 5 — Handle errors gracefully:**

```
classify_episode() is called once per episode by an external evaluation loop —
it has no control over other calls and cannot "skip to the next one." Its job
is to never raise: always return a valid dict.

Wrap the entire function body in a try/except Exception block:

try:
    # steps 1–4 here
    return {"label": label, "reasoning": reasoning}
except Exception as e:
    print(f"[classify_episode] error: {e}")
    return {"label": "unknown", "reasoning": f"error: {e}"}

Specific failures this catches:
- Network/API error from _client.chat.completions.create()
- json.JSONDecodeError if the model returns malformed JSON
- KeyError if the JSON is valid but missing "label" or "reasoning" keys

The evaluation loop gets a valid dict every time and keeps running.
```
---

### Return value structure

```python
{
    "label": str,      # one of VALID_LABELS, or "unknown" if invalid/error
    "reasoning": str,  # brief explanation from the LLM
}
```

---

## Notes on label quality

The classifier is only as good as your labels. If your training examples have
inconsistent or ambiguous labels, the LLM will learn the wrong pattern.

Before implementing the classifier, re-read `data/taxonomy.md` and double-check
any labels you're unsure about. Annotation quality is part of the lab.

---

## Implementation Notes

*Fill this in after implementing and testing both functions.*

**Test: what does the raw LLM response look like for one episode?**

```
Episode tested: The Aral Sea: A Disaster in Four Acts
Raw response text (response.choices[0].message.content):
{"label": "narrative", "reasoning": "The episode tells a story assembled from
external sources, including historical events and possibly interviews, with a
clear narrative arc about the decline of the Aral Sea."}
```

**How did you parse the label out of the response?**

```
1. raw_text.strip() — remove leading/trailing whitespace
2. Check if cleaned text starts with ``` — if so, strip the opening fence
   (including the optional "json" language tag) and the closing ```
3. json.loads(cleaned) — parse into a dict
4. parsed["label"].strip().lower() — normalize the label string
5. Check normalized label against VALID_LABELS — set to "unknown" if not found
```

**Did any episodes return `"unknown"`? If so, why?**

```
No — every episode returned a valid label. The model consistently output clean
JSON with a label from the four valid options.
```

**One thing about the output format that surprised you:**

```
The model returned clean JSON in the content field with no markdown fences —
the fence-stripping code was not needed for this run. What was surprising is
that the full response object (ChatCompletion) contains a large amount of
metadata (token counts, timing, model fingerprint, etc.) beyond the content
field, which is the only part classify_episode() actually uses.
```
