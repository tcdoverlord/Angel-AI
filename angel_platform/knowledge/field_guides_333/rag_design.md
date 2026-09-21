# Retrieval-Augmented Generation

1. Index documents with stable identifiers, titles, hashes, and source paths.
2. Retrieve a small set of relevant passages instead of dumping the entire library into every prompt.
3. Keep retrieved evidence separate from system instructions and clearly label it as reference context.
4. When retrieval returns nothing useful, say so rather than filling the gap with confident guesses.
5. Re-index when a document hash changes and preserve the previous index until the new one is valid.

## Verification questions

- What evidence was collected?
- What changed, if anything?
- Can the operation be reversed?
- What requires the user's explicit approval?
