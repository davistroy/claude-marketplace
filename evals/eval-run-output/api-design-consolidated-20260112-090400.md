# API Design: External Data Access — Consolidated Recommendation

**Consolidated from:**
- `multi-variant-a.md` — REST Approach (Alex, Backend Team, 2026-01-10)
- `multi-variant-b.md` — GraphQL Approach (Jordan, Frontend Team, 2026-01-11)

**Consolidated:** 2026-01-12
**Status:** Decision document

---

## Summary of Proposals

Two competing proposals were submitted for the Daily Standup Bot's external data access API. Both documents agree on the product goal (allow third-party integrations to retrieve standup summaries and team participation data) and on the authentication approach (OAuth 2.0 Bearer token). They diverge on API style and v1 scope.

Both proposals independently reached the **same v1 recommendation: REST**. GraphQL was proposed as the better long-term fit for a diverse integration ecosystem, with the shared caveat that v1's narrow integration surface doesn't justify the implementation overhead.

---

## Where the Proposals Agree

| Topic | Both Proposals Say |
|-------|--------------------|
| Authentication | OAuth 2.0 Bearer token in `Authorization` header |
| v1 recommendation | REST is the right choice for v1 |
| GraphQL long-term | GraphQL is better if integration complexity grows |
| v1 scope | Single integration use case; REST overhead is justified |
| Versioning | Additive changes (new fields, optional params) are non-breaking |

---

## Where the Proposals Diverge

| Topic | REST (Alex) | GraphQL (Jordan) |
|-------|-------------|------------------|
| Data fetching | Multiple round trips for related resources | Single query, any shape |
| Over-fetching | Present — clients receive full resource objects | Eliminated |
| Real-time | Polling only | Native subscriptions |
| Caching | HTTP cache headers work natively on GET | Harder at HTTP layer (POST) |
| Team expertise | High — familiar to all devs | Low — no production experience |
| Implementation cost | Lower | Higher (requires Apollo/Yoga) |
| Self-documentation | Swagger/OpenAPI | GraphQL introspection |

---

## Decision: REST for v1, GraphQL evaluation at v2

Both proposals converge on this recommendation, and it is the correct one for the following reasons:

1. **Team capability:** The team has REST experience; no one has GraphQL production experience. A technology choice that introduces a learning curve at the same time as a new product launch adds unnecessary risk.

2. **Integration surface:** v1 serves a single integration use case. GraphQL's advantages (no over-fetching, single round trip) become material at 5+ diverse client types with heterogeneous data needs, not at one.

3. **HTTP caching:** The data model is read-heavy and time-based (daily summaries). REST with HTTP caching provides free performance benefits that a POST-based GraphQL API cannot leverage.

4. **Real-time is not a v1 requirement:** The lack of subscriptions in REST is not a gap at launch. The standup summary model is inherently batch-oriented (collect → summarize → post once per day). Live blockers feed is a v2 product conversation.

---

## Consolidated API Specification

### Authentication

OAuth 2.0 Bearer token. Token endpoint: `POST /v1/auth/token` (client credentials grant). Expiry: 24 hours with automatic refresh.

All endpoints require `Authorization: Bearer <token>` header.

### Endpoints

#### Summaries

```
GET /v1/teams/{team_id}/summaries
GET /v1/teams/{team_id}/summaries/{date}
GET /v1/teams/{team_id}/summaries/{date}/responses
```

- `{date}` in ISO 8601 format (YYYY-MM-DD)
- Pagination: `?page=1&per_page=20`
- Filtering: `?has_blockers=true`

#### Team Management

```
GET    /v1/teams/{team_id}/members
POST   /v1/teams/{team_id}/members
DELETE /v1/teams/{team_id}/members/{user_id}
```

### Versioning

URL path prefix (`/v1/`). Breaking changes require a new major version path (`/v2/`). Non-breaking additions (new optional fields, new optional query params) do not require a version bump. Both proposals agree on this approach.

---

## v2 Trigger: When to Revisit GraphQL

Revisit the GraphQL option when **two or more** of these conditions are met:
- Three or more distinct integration partners with different data shape requirements
- Real-time blockers feed is on the product roadmap
- The engineering team has gained GraphQL production experience on a lower-stakes service
- The REST API has measurable over-fetching complaints from integration partners

---

## Sources

This document synthesizes `multi-variant-a.md` (REST proposal) and `multi-variant-b.md` (GraphQL proposal). The REST endpoint specification is drawn from variant A. The divergence analysis and v2 trigger criteria are synthesized from both documents.
