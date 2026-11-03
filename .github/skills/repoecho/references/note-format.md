# Note format

Supply this JSON to `remember --note FILE --receipt ID`. Copilot writes the knowledge; the helper attaches source hashes, scope digests, policy fingerprint and timestamps. Do not insert your own evidence/timestamps into note JSON.

```json
{
  "id": "process-lifecycle",
  "title": "Process manager lifecycle and shutdown",
  "summary": "Concise explanation grounded in the captured source files.",
  "facts": [
    "src/main/java/example/ProcessManager.java:42 owns the process registry."
  ],
  "inferences": [
    "The registry appears intended to be process-local; persistence was not established."
  ],
  "tags": ["java", "process", "lifecycle", "shutdown"],
  "caveats": [
    "No integration test was run; this note describes inspected source only."
  ]
}
```

The example paths/claims are illustrative: replace them with facts from the actual capture. Required: `id` (1–80 chars, lowercase letters/digits/dot/underscore/hyphen, starts with letter/digit), `title` (1–160 chars), `summary` (1–4,000 chars). Optional arrays of strings: `facts`, `inferences`, `tags`, `caveats`. Whole note limit: 16,000 serialized characters. Unknown fields are rejected. Aim for 150–400 words per note and a handful of concrete source references.

One capture receipt binds one note to every captured file. Prefer separate captures for independent notes. A receipt records exactly the bytes presented to the agent, plus explicitly declared scope contents. A note is rejected if that evidence changed before save. Receipts carry hashes, not source contents, and expire after 24 hours.

Useful stable IDs include `orientation`, `build-and-test`, `module-orders`, `api-process-lifecycle`, `test-process-manager`, and `concurrency-contract`. Reuse the logical ID after relearning; the helper versions it by evidence hash and retains bounded history for branch switching. Identical evidence replaces the same revision. Cache application architecture, build entry points, component responsibilities, verified invariants and known gaps. Do not cache scratch plans, credentials, absolute workstation paths, or claims about remote services as if they were repository facts.

For cross-module conclusions, capture both sides of the contract. For claims such as “only implementation” or “all modules”, declare the matching scope and inspect enough evidence to justify the claim. Include the file that controls registration/discovery as a source. A scope digest catches future additions/deletions/edits but is not itself evidence of semantic understanding.

## Workflow-specific notes

Prefer a stable topic such as `workflow-shutdown` or `workflow-config-reload` over appending every discovery to `orientation`. In the existing summary/facts fields, explain the trigger, ordered steps, responsible classes/methods, cross-module handoffs, relevant configuration, failure paths and known gaps. Include only details established by captured evidence; omit irrelevant categories. Use workflow terms and actual identifiers in the title/tags. These are writing guidelines, not additional JSON fields.

When a follow-up reveals a missing dependency or step, capture and read the expanded evidence and update the same topic. Split a note only when separate workflows need independent evidence or become hard to retrieve clearly. A sufficient verified workflow note should support an explanation without reopening every cited file; edits still require current source inspection. Keep source references and caveats precise enough to show when additional reading is necessary.
