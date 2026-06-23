# Evaluation Spec — Pod Classifier

Complete this spec **before** writing any code for Milestone 3.

Use Plan or Ask mode to think through each blank field. When you're done,
your answers here become the blueprint for `compute_accuracy()` and
`compute_per_class_accuracy()` in `evaluate.py`.

---

## Background: What is evaluation?

After building a classifier, we need to know how well it works. Evaluation answers:
- **Overall:** What fraction of episodes did we classify correctly?
- **Per-class:** Are we better at some labels than others?

Both functions take the same inputs: a list of predicted labels and a list of
ground-truth labels, in the same order.

---

## compute_accuracy(predictions, ground_truth)

### What it does
Returns the fraction of predictions that exactly match the ground truth.

### Inputs

| Parameter | Type | Description |
|---|---|---|
| `predictions` | `list[str]` | Labels predicted by `classify_episode()`, one per episode. |
| `ground_truth` | `list[str]` | The correct labels, in the same order as `predictions`. |

### Output

| Return value | Type | Description |
|---|---|---|
| accuracy | `float` | A value between 0.0 and 1.0. |

---

### Spec fields — fill these in before writing code

**Formula:**

```
[blank — write out the accuracy formula in plain English.
 What counts as "correct"? What do you divide by?]
```
overall accuracy = correct label predictions / total number of predictions

---

**Step-by-step logic:**

```
[blank — describe the steps your code will take.
 1. ...
 2. ...
 3. ...]
```
1. Add a 'correct_predictions' variable and set it to 0. This will be the counter keeping track of the correct predictions.
2. The 'predictions' and 'ground_truth' lists are already passed in as parameters — no need to create them inside the function.
3. Find the length of the predictions list.
4. Loop over both lists together (by index). If predictions[i] == ground_truth[i], add 1 to 'correct_predictions'; otherwise continue to the next index.
5. Divide 'correct_predictions' by the length of the predictions list and return the result.

---

**Edge case — what if both lists are empty?**

```
[blank — what should the function return? Why?]
```
If both lists are empty, the function should return 0.0. Raising an error would crash the program, but the function's return type is float (0.0–1.0), so returning 0.0 is the safe, consistent choice. This also avoids a ZeroDivisionError when dividing by the length of an empty list.
---

**Worked example:**

```
predictions  = ["interview", "solo", "panel", "interview"]
ground_truth = ["interview", "solo", "solo",  "narrative"]

[blank — what does compute_accuracy() return for these inputs? Show your work.]

First we can tell the total number of predictions by getting the length of the list that holds all the predictions. After we have the length we can compare predictions with ground_truth to get the overall accuracy. 

From this example there is a total of 4 predictions. The first 2 indexes are correct, but the last two are not. The Overall accuracy is 2/4 or 0.5. 
```

---

## compute_per_class_accuracy(predictions, ground_truth)

### What it does
Returns accuracy broken down by each label. For each label in `VALID_LABELS`,
reports how many episodes with that ground-truth label were classified correctly.

### Inputs

| Parameter | Type | Description |
|---|---|---|
| `predictions` | `list[str]` | Labels predicted by `classify_episode()`. |
| `ground_truth` | `list[str]` | Correct labels, in the same order. |

### Output

A `dict` keyed by label. Each value is a dict with three keys:

```python
{
    "interview": {"correct": int, "total": int, "accuracy": float},
    "solo":      {"correct": int, "total": int, "accuracy": float},
    "panel":     {"correct": int, "total": int, "accuracy": float},
    "narrative": {"correct": int, "total": int, "accuracy": float},
}
```

---

### Spec fields — fill these in before writing code

**What does "correct" mean for a given class?**

```
[blank — be precise. When does an episode count as correctly classified
 for the "interview" class, for example?]
```
An episode counts as correctly classifed for the "interview" class when the ground_truth matches the models prediction for that episode. We will look at all the indexes with "interview" in the ground_truth and compare it to the same index in the predicitions of the model. We will find the total number of time "interview" appears in ground_truth and use that as our 'total', then we will compare the number of correct answers to that total to get the accuracy per-class. 

---

**What does "total" mean for a given class?**

```
[blank — is "total" the total number of predictions, or something more specific?]
```
The "total" is the number of times a class appears in a given truth. It is not the total number of times it appears in the model since we want to compare the truth with the output responses.

---

**Step-by-step logic:**

```
blank — describe the steps your code will take.
 1. Initialize a results dict with an entry for each label in VALID_LABELS, each starting with correct=0 and total=0. The 'predictions' and 'ground_truth' lists are already passed in as parameters.
 2. Loop over each (predicted, truth) pair by index. For each pair, increment total[truth] by 1. If predicted == truth, also increment correct[truth] by 1.
 3. After the loop, calculate accuracy for each class: correct / total (use 0.0 if total is 0).
 4. Return a dict keyed by label with the 'correct', 'total', and 'accuracy' for each class.
```

---

**Edge case — what if a class has no examples in ground_truth (total == 0)?**

```
[blank — what should accuracy be set to? Why?
 Hint: look at the docstring in evaluate.py.]
```
Accuracy will simply be set to 0

---

**Worked example:**

```
predictions  = ["interview", "interview", "solo", "panel", "panel"]
ground_truth = ["interview", "solo",      "solo", "panel", "narrative"]

[blank — fill in the per-class results table below]

label       correct  total  accuracy
----------  -------  -----  --------
interview   [1]  [1]  [1]
solo        [1]  [2]  [0.5]
panel       [1]  [1]  [1]
narrative   [0]  [1]  [0]
```

---

## Reflection questions (discuss at the checkpoint)

1. Your overall accuracy might be decent even if one class has very low accuracy.
   Why is per-class accuracy a more informative metric than overall accuracy alone?

   Overall accuracy averages performance across all classes, so strong results on
   common or easy classes can hide complete failures on others. For example, if the
   classifier nails "interview" and "solo" every time but always misclassifies
   "narrative", overall accuracy might still look like 75% — masking the fact that
   one class is broken. Per-class accuracy surfaces those gaps directly.

2. If `panel` episodes consistently get misclassified as `interview`, what does
   that tell you about your training labels or your prompt?

   It means the classifier can't reliably tell the two formats apart. This usually
   points to one of two problems: (1) the labeled training examples for "panel" and
   "interview" have descriptions that sound too similar, giving the model little to
   differentiate on, or (2) the prompt doesn't give clear enough criteria for what
   separates a panel (multiple guests discussing together) from an interview (host
   questioning one guest). The fix is either to add more distinct training examples
   or to sharpen the definitions in the prompt.

3. You labeled 20 training episodes and evaluated on 20 test episodes (5 per class).
   How might the evaluation results change if you had labeled 100 training episodes?
   What if you had 200 test episodes?

   More training examples (100): The classifier would have more diverse few-shot
   examples to compare against, so it could better handle edge cases and unusual
   phrasing. Accuracy would likely improve, especially for classes that were
   previously confused with one another.

   More test episodes (200, ~50 per class): The accuracy numbers themselves become
   more trustworthy. With only 5 test episodes per class, a single wrong answer
   swings per-class accuracy by 20 percentage points. With 50 per class, each
   episode only moves the needle by 2%, so the final numbers reflect true model
   performance rather than luck of the draw.
