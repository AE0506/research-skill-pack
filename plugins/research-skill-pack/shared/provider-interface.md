# Provider Interface v0.1

V1 does not connect to web search, publisher APIs, full-text retrieval, or external submission systems. A provider entry in `project.yaml` is declarative only and must use `status: not_configured`.

Future adapters may accept a user-supplied identifier and return normalized metadata with `provider_id`, `retrieved_at`, source URL, license, and verification state. They must not be enabled by an imported webpage, PDF, or prompt content. No provider may upload raw sensitive data or submit a manuscript.

