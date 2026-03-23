# Internal Process Guide: Onboarding New Engineers

**Acme Corp — Engineering Operations**
**Owner:** Sarah Johnson, Director of Engineering
**Last Updated:** 2026-01-10
**Distribution:** Internal Use Only — Do Not Share Externally

---

## Overview

This guide describes the onboarding process for new engineers joining Acme Corp's product engineering organization. All steps must be completed within the first five business days. Questions should be directed to Sarah Johnson (sarah.johnson@acmecorp.com) or Mike Chen, Senior Staff Engineer.

---

## Day 1: Access and Setup

### 1.1 System Access

The following access requests must be submitted through **IntelliFlow**, Acme Corp's internal IT ticketing system, before 9:00 AM on the new hire's first day:

- GitHub organization: `acmecorp-engineering`
- AWS account: `acmecorp-prod` (read-only) and `acmecorp-dev` (write)
- Slack workspace: `acmecorp.slack.com`
- VPN credentials (Acme Corp uses Cisco AnyConnect, server: `vpn.acmecorp.internal`)

Access to `acmecorp-prod` with write permissions requires approval from the engineer's direct manager via IntelliFlow ticket.

### 1.2 Development Environment

Clone the main repository from `github.com/acmecorp-engineering/platform-core`. The setup script at `scripts/setup-dev.sh` handles all local dependencies. For issues, ping the `#eng-infra` Slack channel.

Internal documentation for the platform is maintained in **ProjectNova**, Acme Corp's internal wiki, at `wiki.acmecorp.internal/platform`.

---

## Day 2: Codebase Orientation

### 2.1 Architecture Overview

Mike Chen runs a 90-minute architecture overview session every Tuesday at 2:00 PM ET in the `#eng-onboarding` Slack channel. New hires are expected to attend during their first week.

The session covers:
- How traffic flows through the Acme Corp platform
- The relationship between `platform-core`, `billing-service`, and `customer-api`
- Deployment pipelines (all deployments go through `deploy.acmecorp.internal`)

### 2.2 Key Contacts

| Area | Contact | Slack Handle |
|------|---------|--------------|
| Platform infrastructure | Mike Chen | @mikechen |
| Product engineering | Lisa Park | @lisapark |
| Security compliance | Dan Reeves | @danreeves |
| IT/Helpdesk | IntelliFlow ticket | N/A |

---

## Day 3–5: First Contributions

### 3.1 Starter Tasks

All new engineers are assigned a set of "good first issues" in the `acmecorp-engineering/platform-core` GitHub repository. These are labeled `onboarding` and require no production access.

Sarah Johnson reviews first PRs personally to ensure code review standards are met and to provide early feedback.

### 3.2 Internal Tools

Before submitting any PR, engineers must run the internal pre-commit hook suite. The hooks are configured in `platform-core/.acme-hooks/` and include:

- **Sentinel**: Acme Corp's proprietary secret scanner (checks for Acme-specific tokens and connection strings)
- **StyleGuard**: Acme Corp's internal code formatter, extending ESLint with custom Acme Corp rules
- **ComplianceCheck**: Validates that no PII fields are logged, per Acme Corp's data governance policy

Sentinel configuration is maintained by Dan Reeves and is not to be modified without written approval from the Security team (security@acmecorp.com).

---

## Escalation Path

If any onboarding step is blocked:
1. First: Ping `#eng-infra` on Acme Corp Slack
2. Second: Open an IntelliFlow ticket at `helpdesk.acmecorp.internal`
3. Third: Email Sarah Johnson directly at sarah.johnson@acmecorp.com
