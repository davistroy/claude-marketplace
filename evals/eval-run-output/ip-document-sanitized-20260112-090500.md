# Internal Process Guide: Onboarding New Engineers

**[Company] — Engineering Operations**
**Owner:** [Engineering Director], Director of Engineering
**Last Updated:** 2026-01-10
**Distribution:** Internal Use Only — Do Not Share Externally

---

## Overview

This guide describes the onboarding process for new engineers joining [Company]'s product engineering organization. All steps must be completed within the first five business days. Questions should be directed to [Engineering Director] ([engineering-director]@[company-domain]) or [Senior Staff Engineer], Senior Staff Engineer.

---

## Day 1: Access and Setup

### 1.1 System Access

The following access requests must be submitted through **[IT Ticketing System]**, [Company]'s internal IT ticketing system, before 9:00 AM on the new hire's first day:

- GitHub organization: `[company]-engineering`
- AWS account: `[company]-prod` (read-only) and `[company]-dev` (write)
- Slack workspace: `[company].slack.com`
- VPN credentials ([Company] uses Cisco AnyConnect, server: `vpn.[company-domain].internal`)

Access to `[company]-prod` with write permissions requires approval from the engineer's direct manager via [IT Ticketing System] ticket.

### 1.2 Development Environment

Clone the main repository from `github.com/[company]-engineering/platform-core`. The setup script at `scripts/setup-dev.sh` handles all local dependencies. For issues, ping the `#eng-infra` Slack channel.

Internal documentation for the platform is maintained in **[Internal Wiki Tool]**, [Company]'s internal wiki, at `wiki.[company-domain].internal/platform`.

---

## Day 2: Codebase Orientation

### 2.1 Architecture Overview

[Senior Staff Engineer] runs a 90-minute architecture overview session every Tuesday at 2:00 PM ET in the `#eng-onboarding` Slack channel. New hires are expected to attend during their first week.

The session covers:
- How traffic flows through the [Company] platform
- The relationship between `platform-core`, `billing-service`, and `customer-api`
- Deployment pipelines (all deployments go through `deploy.[company-domain].internal`)

### 2.2 Key Contacts

| Area | Contact | Slack Handle |
|------|---------|--------------|
| Platform infrastructure | [Senior Staff Engineer] | @[senior-staff-engineer] |
| Product engineering | [Product Engineering Lead] | @[product-engineering-lead] |
| Security compliance | [Security Lead] | @[security-lead] |
| IT/Helpdesk | [IT Ticketing System] ticket | N/A |

---

## Day 3–5: First Contributions

### 3.1 Starter Tasks

All new engineers are assigned a set of "good first issues" in the `[company]-engineering/platform-core` GitHub repository. These are labeled `onboarding` and require no production access.

[Engineering Director] reviews first PRs personally to ensure code review standards are met and to provide early feedback.

### 3.2 Internal Tools

Before submitting any PR, engineers must run the internal pre-commit hook suite. The hooks are configured in `platform-core/.[company]-hooks/` and include:

- **[Secret Scanner]**: [Company]'s proprietary secret scanner (checks for [Company]-specific tokens and connection strings)
- **[Code Formatter]**: [Company]'s internal code formatter, extending ESLint with custom [Company] rules
- **[Compliance Checker]**: Validates that no PII fields are logged, per [Company]'s data governance policy

[Secret Scanner] configuration is maintained by [Security Lead] and is not to be modified without written approval from the Security team ([security-team]@[company-domain]).

---

## Escalation Path

If any onboarding step is blocked:
1. First: Ping `#eng-infra` on [Company] Slack
2. Second: Open a [IT Ticketing System] ticket at `helpdesk.[company-domain].internal`
3. Third: Email [Engineering Director] directly at [engineering-director]@[company-domain]
