# QSense CLI V1 Design

> **Status**: V1 scope has been expanded beyond the original image-only design.
> Current implementation supports **image, audio, and video understanding** with
> a curated multi-model registry. See `README.md` and `docs/usage.md` for the
> current state. This document is retained as the original design rationale.

## Goal

Build a minimal CLI-first image understanding tool for agents.

V1 was originally scoped as intentionally narrow:

- Image understanding only
- Support one or more images in a single request
- Keep the command surface small
- Guide first-time users through configuration
- Store configuration globally so later runs need no setup

The scope was later expanded to include audio and video understanding while preserving the same minimal CLI philosophy.

## Naming

- Package name: `qsense-cli`
- Binary name: `qsense`

The name avoids locking the long-term direction to vision only, while V1 remains image-only.

## Command Shape

Primary command:

```bash
qsense --prompt "..." --image <path-or-url> [--image <path-or-url> ...]
```

Optional flags kept in V1:

```bash
--prompt
--image
--model
--timeout
--help
```

Examples:

```bash
qsense --prompt "Describe this screenshot" --image screenshot.png
```

```bash
qsense --prompt "Compare these images" --image before.png --image after.png
```

```bash
qsense --model gemini-3-flash-preview --prompt "Summarize the common elements" --image a.png --image b.png --image c.png
```

## Input Rules

- `--prompt` is required
- At least one `--image` is required
- `--image` may be repeated to support multi-image analysis
- V1 is designed for a stable range of 1-5 images per request
- Image order is preserved and passed to the model in the same order
- Each image may be a local file path or a remote `http/https` URL

Supported local image formats in V1:

- `.jpg`
- `.jpeg`
- `.png`
- `.webp`
- `.gif`

Unsupported image types should fail with a clear error.

## Configuration

Configuration priority:

1. Command-line flags
2. Process environment variables
3. Global user config file

Global config location:

```bash
~/.qsense/.env
```

Stored keys:

```env
QSENSE_API_KEY=...
QSENSE_BASE_URL=https://api.openai.com/v1
QSENSE_MODEL=gemini-3-flash-preview
```

CLI flags override these stored defaults when provided.

## First-Run Setup

If required configuration is missing, V1 should behave differently for interactive and non-interactive environments.

Interactive terminal behavior:

1. Prompt for API key
2. Prompt for base URL, with the current default prefilled or explained
3. Prompt for default model, with the current default prefilled or explained
4. Create `~/.qsense/` if needed
5. Write the values into `~/.qsense/.env`

Non-interactive behavior:

- Do not prompt
- Exit with an error
- Tell the user to initialize `qsense` once in an interactive terminal first

This keeps first-time setup easy for humans while preventing agent jobs from hanging.

## Runtime Flow

V1 should stay close to the current prototype and avoid unnecessary internal layers.

Runtime steps:

1. Parse CLI arguments
2. Load configuration from flags, environment, and global `.env`
3. If needed, run first-time interactive setup
4. Normalize image inputs
5. Build one OpenAI-compatible request
6. Print the assistant text result

### Image Normalization

For each `--image` value:

- If it is a remote `http/https` URL, pass it through directly
- If it is a local path, resolve it to an absolute path
- Verify the file exists
- Infer MIME type from extension
- Read the file and convert it into a data URL

### Request Construction

The request remains a single user message with one text item followed by one image item per input.

Conceptually:

```json
[
  { "type": "text", "text": "Compare these images" },
  { "type": "image_url", "image_url": { "url": "..." } },
  { "type": "image_url", "image_url": { "url": "..." } }
]
```

This keeps the implementation small while fully supporting multi-image prompting.

## Output Behavior

V1 outputs plain text only.

Success behavior:

- Print only the final assistant text to stdout
- End with a trailing newline

Failure behavior:

- Print a single clear error message to stderr
- Exit with status code `1`

V1 does not include JSON output mode.

## Error Cases

Errors should stay simple and explicit.

Examples:

```text
[qsense] --prompt is required.
```

```text
[qsense] At least one --image is required.
```

```text
[qsense] Image file not found: /path/to/a.png
```

```text
[qsense] Unsupported image type: /path/to/a.bmp
```

```text
[qsense] Missing API key. Run qsense once in an interactive terminal to initialize ~/.qsense/.env.
```

```text
[qsense] HTTP 401: ...
```

```text
[qsense] No assistant text found in response.
```

## Out of Scope

The following are intentionally excluded from V1:

- Audio understanding
- Video understanding
- Structured JSON output
- Subcommands such as `probe` or `models`
- Schema extraction workflows
- Advanced provider abstraction
- Large-scale batching beyond the recommended 1-5 image range

## Implementation Notes

The current `vision.js` prototype can evolve into V1 with minimal reshaping:

- Keep repeated-flag parsing for `--image`
- Require `--prompt`
- Rename command identity from `qvision` to `qsense`
- Replace per-run API key expectation with global config lookup and first-run setup
- Keep the current OpenAI-compatible `/chat/completions` request pattern
- Keep plain-text stdout as the only success output mode

This design intentionally favors a small, stable script over early abstraction.
