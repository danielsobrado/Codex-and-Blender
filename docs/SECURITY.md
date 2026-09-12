# Security model

## Core assumption

Blender automation is code execution inside the Blender process. MCP does not make that execution inherently safe.

Blender's own MCP documentation advises caution around model-generated Python and recommends isolating sensitive environments.

Reference:
https://www.blender.org/lab/mcp-server/

## Trust boundaries

```text
Codex / agent
   |
   | MCP
   v
MCP server process
   |
   | local bridge
   v
Blender add-on
   |
   v
Blender Python runtime
   |
   v
permissions/resources available to Blender
```

The important boundary is the Blender process itself.

Do not assume a sandbox applied to a separate agent shell automatically constrains an already-running Blender instance.

## Recommended tiers

### Normal development

- dedicated project directory;
- Git/versioned source;
- backups/checkpoints for valuable `.blend` files;
- structured/read-oriented MCP tools preferred;
- broad code-execution tools disabled unless needed;
- no secrets stored in project configuration.

### Autonomous or less-trusted experimentation

Prefer a disposable VM or similarly isolated environment containing:

- Blender;
- MCP bridge/server;
- Codex/agent runtime;
- a disposable repository checkout;
- only the assets required for the task.

Keep sensitive credentials and unrelated personal/work files outside that environment.

Restrict network access unless a task genuinely needs it.

## Tool policy

Use the least-powerful tool that answers the question.

Preferred order:

1. scene/object summaries;
2. file/dependency checks;
3. screenshots and viewport rendering;
4. project-specific constrained mutations;
5. broad Blender Python execution only when justified.

A future project-specific MCP layer should expose narrow operations such as camera/transform/material updates and validation rather than relying on generic Python for routine work.

## Repository protections

- Generated files stay under `output/`.
- Source assets should not be overwritten as build outputs.
- Managed scene ownership prevents broad object deletion when working from an existing `.blend`.
- Local `.codex/config.toml` is ignored so machine-specific settings are not accidentally committed.

## Agent approval model

Codex supports approval/sandbox controls for its own actions. Use those controls as defense in depth, while continuing to treat Blender as a separate process boundary.

Reference:
https://developers.openai.com/codex/agent-approvals-security

## External content

Treat imported assets, `.blend` files, add-ons and prompts from external sources as untrusted inputs until reviewed.

For production environments:

- pin known versions;
- prefer trusted asset sources;
- inspect add-ons before enabling them;
- avoid automatically granting broad capabilities based on instructions contained inside external content.
