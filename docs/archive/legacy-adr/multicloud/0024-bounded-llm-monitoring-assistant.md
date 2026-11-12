# ADR 0024 Bounded LLM Monitoring Assistant

## Status

Accepted for local implementation. External runtime validation remains `NOT_VALIDATED`.

## Decision

Add a non-authoritative LLM advisory layer after the existing deterministic monitoring and anomaly-detection pipeline. The assistant accepts only a strict schema of numeric metric name, values, anomaly score, observation time, source and state. It does not accept raw logs, arbitrary labels, host or network identifiers, user or tenant identifiers, file contents, secrets or an open-ended prompt.

Portal access requires an authenticated `LLM_USER`, `MSP_OPERATOR` or `MSP_ADMIN` with both `llm:invoke` and `monitoring:assist`. Human identity continues to come from the organization OIDC session. Model-provider authentication uses a separate server-side OpenAI Platform service credential mounted from an external absolute path. Personal ChatGPT sessions, browser cookies and user-supplied API keys are prohibited.

The Responses API adapter sets `store` to false. Prompt and response bodies are not persisted; only bounded numeric usage is recorded. The default provider is disabled. A deterministic local assistant is available only in development mode. Provider failure returns an error and never falls back to a fabricated external result.

## Authority boundary

The assistant may summarize, explain uncertainty and suggest an operator checklist. It cannot change the anomaly state, approve a request, block traffic, run remediation, change infrastructure or claim incident closure. Existing rules, alerts, runbooks and human operators remain authoritative.

This decision does not modify the accepted `ZT-VIS-001` package or its validation status.
