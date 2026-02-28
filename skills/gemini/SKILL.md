---
name: gemini
description: Gemini CLI for one-shot Q&A, summaries, and generation.
homepage: https://ai.google.dev/
metadata:
  {
    "openclaw":
      {
        "emoji": "♊️",
        "requires": { "bins": ["gemini"] },
        "install":
          [
            {
              "id": "npm",
              "kind": "npm",
              "package": "@google/gemini-cli",
              "global": true,
              "label": "Install Gemini CLI (npm)",
            }
          ],
      },
  }
---

# Gemini CLI

Use the Gemini CLI for one-shot generations, summaries, or questions.

## Requirements

- `@google/gemini-cli` installed globally via npm.
- `GEMINI_API_KEY` configured in the environment (OpenClaw already provides this).

## Usage

Use the `-p` or `--prompt` flag for **non-interactive (headless)** execution. This is essential when running inside OpenClaw to avoid hanging in an interactive TTY.

- Basic query: `gemini -p "Explain quantum computing in one paragraph."`
- Use a specific model: `gemini -m gemini-2.5-pro -p "Prompt..."`
- JSON output: `gemini --output-format json -p "Return a list of 5 colors"`

## Extensions and Skills

- List extensions: `gemini --list-extensions`
- Manage extensions: `gemini extensions <command>`
- Manage skills: `gemini skills <command>`

## Notes

- Avoid using the `--yolo` flag unless specifically instructed, for safety reasons.
- The `gemini` command without `-p` starts an interactive TTY chat, which requires `pty:true` if used via the `exec` tool. For simple one-shot answers, always use `-p`.
