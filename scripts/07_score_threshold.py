import sys

sys.path.insert(0, "src")          # let this script import from the src folder
from search import search_with_confidence

IN_SCOPE = [
    "What is a translator?",
    "What is a lexeme?",
    "What are the six phases of a compiler?",
    "What is a perceptron?",
    "What is the Hebbian learning rule?",
    "What is the difference between soft computing and hard computing?",
    "What is an artificial neural network?",
    "What is multi-objective optimization?",
    "What is competitive learning?",
    "What are the prerequisites for this course?",
]

OUT_OF_SCOPE = [
    "Who won the IPL in 2024?",
    "What is the capital of France?",
    "Give me a recipe for chicken biryani.",
    "What is the weather in Dehradun today?",
    "Who is the Prime Minister of India?",
    "Which smartphone should I buy under 20000 rupees?",
    "Write a poem about the moon.",
    "How do I sort a list in Python?",
    "Explain quantum entanglement.",
    "What is the best movie of 2025?",
]


def measure(label, questions):
    print(f"\n=== {label} ===")
    scores = []
    for q in questions:
        _, similarity = search_with_confidence(q)
        scores.append(similarity)
        print(f"{similarity:.3f} | {q}")
    return scores


in_scores = measure("IN SCOPE (should answer)", IN_SCOPE)
out_scores = measure("OUT OF SCOPE (should refuse)", OUT_OF_SCOPE)

print(f"\nLowest in-scope score:     {min(in_scores):.3f}")
print(f"Highest out-of-scope score: {max(out_scores):.3f}")
if min(in_scores) > max(out_scores):
    print("✅ The two groups don't overlap: a clean threshold exists between them.")
else:
    print("⚠️ The groups overlap: no single threshold separates them perfectly.")