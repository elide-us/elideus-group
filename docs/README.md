# Discord Bot Documentation

## Commands

### `!summarize`
Summarize recent messages in the current channel using the `summarize` persona and send the result as a DM.

Example:
```text
!summarize 24
```
This summarizes the past 24 hours of messages.

### `!uwu`
Send a playful uwu-styled response in the channel.

Example:
```text
!uwu hello there
```

## Logging

Each command invocation is logged for auditing:

- **assistant_personas** – stores persona names, prompts, token limits, and model references.
- **assistant_conversations** – records persona usage along with guild/channel/user IDs, model reference, token counts, input text, output text, and timestamps.

The user ID of whoever invokes `!summarize` is captured in the conversation log.

The OpenAI module upserts the persona and appends a conversation record whenever `!summarize` or `!uwu` runs.
