# Discord Bot Documentation

## Commands

### `!summarize`
Summarize recent messages in the current channel and send the result as a DM.

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

- **assistant_personas** – stores persona names and optional metadata.
- **assistant_conversations** – records persona usage along with guild/channel identifiers, input text, output text, and timestamps.

The Discord chat module upserts the persona and appends a conversation record whenever `!summarize` or `!uwu` runs.
