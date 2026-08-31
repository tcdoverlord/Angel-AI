# Angel AI 6.0 — Thinking Status

The chat now keeps a visible animated `● THINKING`, `● THINKING.`, `● THINKING..`,
or `● THINKING...` status while Angel is waiting for the background response.

The indicator starts when Send is pressed and is stopped only when the response
is returned to the UI, including error responses.

This is a UI status indicator only. It does not expose hidden chain-of-thought
or private reasoning.
