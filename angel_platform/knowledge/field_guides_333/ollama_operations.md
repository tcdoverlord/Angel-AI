# Ollama Operations

1. Confirm the local service is reachable before diagnosing a model-specific issue.
2. Distinguish an installed model from a loaded model and from a successful generation.
3. Use small test prompts to measure latency, context handling, and instruction following.
4. Do not claim that a local model performed an external lookup unless a verified connector result exists.
5. Keep model selection configurable so a smaller local model can remain available for offline use.

## Verification questions

- What evidence was collected?
- What changed, if anything?
- Can the operation be reversed?
- What requires the user's explicit approval?
