# API Design Proposal: External Data Access — GraphQL Approach

**Author:** Frontend Team (Jordan)
**Date:** 2026-01-11
**Status:** Proposal for discussion

---

## Overview

This document proposes a GraphQL-based API design for the Daily Standup Bot's external data access layer. GraphQL addresses several limitations of REST that will become apparent as our integration ecosystem grows.

## Design Philosophy

GraphQL lets clients request exactly the data they need in a single query, eliminating over-fetching and multiple round trips. For integration partners building dashboards or analytics tools on top of our API, this is a significant developer experience improvement.

## Proposed Schema

```graphql
type Query {
  team(id: ID!): Team
  summary(teamId: ID!, date: String!): Summary
}

type Team {
  id: ID!
  name: String!
  members: [Member!]!
  summaries(from: String, to: String, hasBlockers: Boolean): [Summary!]!
}

type Summary {
  date: String!
  participationRate: Float!
  responses: [Response!]!
  blockers: [Response!]!
}

type Response {
  user: Member!
  yesterday: String
  today: String
  blockers: String
  submittedAt: String
  isLate: Boolean!
}

type Member {
  id: ID!
  name: String!
  slackId: String!
}
```

## Authentication

Same OAuth 2.0 Bearer token approach as any REST alternative. GraphQL is transport-agnostic; we send tokens in the `Authorization` header.

## Real-Time Support

GraphQL subscriptions provide a natural extension point for live blockers feed without polling:

```graphql
subscription {
  blockerReported(teamId: ID!) {
    user { name }
    blockers
    reportedAt
  }
}
```

## Strengths

- Single endpoint, one round trip to get all related data
- Clients request only the fields they need (no over-fetching)
- Introspection provides self-documenting API out of the box
- Subscription support enables real-time features without a separate WebSocket API
- Strong typing catches integration errors at the schema level

## Weaknesses

- Higher initial implementation cost; requires a GraphQL server (Apollo or Yoga)
- Team has no GraphQL production experience — learning curve
- Harder to cache at the HTTP layer (POST-based queries)
- Complexity overkill if external integration surface stays narrow

## Recommendation

GraphQL is the better long-term choice if we expect many integration partners building diverse clients. For v1 with a single integration use case, the overhead may outweigh the benefits. Recommend REST for v1 with a plan to revisit at v2 if integration complexity grows.
