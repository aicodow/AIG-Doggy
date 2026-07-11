# Security Policy

## Supported Versions

|Version|Supported|
|-|-|
|0.1.x|:white\_check\_mark:|

## Reporting a Vulnerability

**Do not open a public issue.**  
Send details to: aicodow@proton.me

Please include:

* Description of the vulnerability
* Steps to reproduce
* Affected versions
* Suggested fix (if any)

We aim to respond within 48 hours and release a fix within 7 days.

## Security Design

AIG-Doggy is a security gateway deployed in front of LLMs. It does not store user conversation content — only request metadata and sanitized summaries are logged for auditing.

Key security measures:

* API Keys are SHA-256 hashed before storage
* PII detected in inputs/outputs is masked or blocked
* TLS 1.3 for all network communication
* Audit logs are immutable (append-only)
* No plaintext secrets in configuration files (environment variables only)

