# Security Policy

## Reporting Security Issues

If you discover a security vulnerability in multica-py, please **do not** open a GitHub issue. Instead, email the maintainer directly:

**Email**: maximchik.alexandr@yandex.ru

Please include:

- Description of the vulnerability
- Steps to reproduce (if applicable)
- Potential impact
- Suggested fix (if you have one)

## Supported Versions

| Version | Supported          |
|---------|-------------------|
| 0.1.x   | ✅ Current        |

## Scope

The SDK wraps an external `multica` binary via `subprocess`. The upstream `auth login` accepts the token only on argv, so the token is briefly visible to other local users via `ps`/`/proc/<pid>/cmdline` while the login process is running. Redaction scrubs it from logs and `CommandExecutionError` payloads, but on a shared host treat the live process as observable. See [README.md](README.md#security-notes) for the full notes.