# API Design Proposal: External Data Access — REST Approach

**Author:** Backend Team (Alex)
**Date:** 2026-01-10
**Status:** Proposal for discussion

---

## Overview

This document proposes a REST-based API design for the Daily Standup Bot's external data access layer. The API will allow third-party integrations to retrieve standup summaries and team participation data.

## Design Philosophy

REST aligns with our existing internal APIs and team expertise. Resource-based URLs are self-documenting and easy to consume with any HTTP client. Versioning via URL prefix (`/v1/`) gives us a clear migration path.

## Proposed Endpoints

### Summaries

```
GET /v1/teams/{team_id}/summaries
GET /v1/teams/{team_id}/summaries/{date}
GET /v1/teams/{team_id}/summaries/{date}/responses
```

- Returns standup summaries for a given team
- `{date}` in ISO 8601 format (YYYY-MM-DD)
- Pagination via `?page=1&per_page=20` query parameters
- Filtering via `?has_blockers=true`

### Team Management

```
GET  /v1/teams/{team_id}/members
POST /v1/teams/{team_id}/members
DELETE /v1/teams/{team_id}/members/{user_id}
```

## Authentication

OAuth 2.0 with a Bearer token. Tokens issued via `/v1/auth/token` using client credentials grant. Token expiry: 24 hours with automatic refresh.

## Versioning Strategy

Version prefix in URL path. Breaking changes require a new major version. Minor additions (new fields, new optional parameters) are non-breaking and do not require a version bump.

## Strengths

- Familiar to all developers; no special client library needed
- Excellent tooling support (Swagger/OpenAPI, Postman, curl)
- HTTP caching headers work natively for GET endpoints
- Easy to test with standard HTTP clients

## Weaknesses

- Over-fetching: clients may receive more fields than they need
- Multiple round trips required to fetch related resources (team + members + summaries)
- No real-time capability — polling required for live data

## Recommendation

REST is the right choice for v1 given team familiarity and the straightforward, document-centric nature of standup data. Real-time requirements are minimal at launch.
