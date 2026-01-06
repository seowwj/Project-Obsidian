# Security Audit Report

**Date**: 2026-01-06
**Scope**: Frontend Dependencies (`frontend/package.json`)

## Findings

### 1. `protoc-gen-grpc-web` Dependencies
*   **Severity**: High
*   **Vulnerable Packages**: `got`, `http-cache-semantics` (via `download` -> `got` -> `cacheable-request`)
*   **Issues**:
    *   `got`: Allows redirect to UNIX socket (GHSA-pfrx-2q88-qq97).
    *   `http-cache-semantics`: ReDoS vulnerability (GHSA-rc47-6667-2j5j).
*   **Context**: These are **Dev Dependencies** managed by `protoc-gen-grpc-web`. They are used only during the build process to download the `protoc-gen-grpc-web` binary. They are **NOT** bundled into the production application and do not run in the user's browser.
*   **Remediation Status**: `npm audit` reports "No fix available". This implies the upstream `protoc-gen-grpc-web` package needs to update its dependencies.
*   **Action**: Accepted risk. These tools run only on the developer machine during setup/generation.

## Conclusion
The identified vulnerabilities are limited to build-time tools and do not affect the runtime security of the "Project Obsidian" application. We will monitor for upstream updates to `protoc-gen-grpc-web`.
