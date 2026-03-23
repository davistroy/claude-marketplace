# IMPLEMENTATION_PLAN.md

## Project: Daily Standup Bot — MVP

**Generated:** 2026-01-15
**Source:** PRD v1.0 (sample-prd.md)
**Scope:** Phase 1 (Collection) and Phase 2 (Summary) only
**Total Items:** 5 work items across 2 phases

---

## Phase 1: Core Collection Engine

### Item 1.1 — Database Schema and Migration

<!-- STATUS:todo -->

**Status:** todo
**Size:** S
**Files:** `db/migrations/001_initial_schema.sql`, `db/schema.ts`

**Tasks:**
- [ ] Create `workspaces` table (id, slack_team_id, config_json, created_at)
- [ ] Create `roster` table (id, workspace_id, slack_user_id, is_active)
- [ ] Create `responses` table (id, roster_id, date, yesterday, today, blockers, submitted_at, is_late)
- [ ] Create `summaries` table (id, workspace_id, date, posted_at, participation_rate)
- [ ] Add indexes on (workspace_id, date) for responses and summaries
- [ ] Write migration script with rollback

**Acceptance Criteria:**
- Migration runs without error on a fresh PostgreSQL 15 database
- Rollback script returns database to pre-migration state
- All foreign key constraints are enforced
- Schema matches entity relationships in the PRD

**Notes:** Use `node-pg-migrate` for migration management. Schema must support up to 200 roster members per workspace.

---

### Item 1.2 — Slack Prompt Delivery

<!-- STATUS:todo -->

**Status:** todo
**Size:** M
**Files:** `src/scheduler/promptJob.ts`, `src/slack/messageSender.ts`, `src/config/timeZones.ts`

**Tasks:**
- [ ] Implement cron scheduler using `node-cron` with per-workspace offset table
- [ ] Implement staggered DM delivery (max 5 DMs per second to avoid rate limiting)
- [ ] Create standup prompt message template (3 questions, plain text)
- [ ] Handle Slack API errors gracefully (retry once, log failure)
- [ ] Store delivery timestamps in `responses` table on prompt sent

**Acceptance Criteria:**
- Prompts are delivered within 60 seconds of the configured time
- Staggering prevents more than 5 concurrent `im.open` calls per workspace
- Failed deliveries are logged with error details
- Unit tests cover the offset calculation logic for UTC-8 through UTC+9

**Notes:** Dev's spike (due Jan 16) must be completed before implementing this item. See spike doc in `docs/spikes/scheduler-timezone.md`.

---

### Item 1.3 — Response Handler

<!-- STATUS:todo -->

**Status:** todo
**Size:** M
**Files:** `src/slack/eventHandler.ts`, `src/db/responseRepository.ts`

**Tasks:**
- [ ] Handle incoming DM events via Bolt.js `message` listener
- [ ] Parse free-form responses into yesterday/today/blockers fields
- [ ] Handle "skip" response: mark user as skipped, do not include in summary
- [ ] Detect blockers: if `blockers` field is non-empty, set `has_blocker = true`
- [ ] Mark responses as late if submitted after collection window close
- [ ] Persist response to database

**Acceptance Criteria:**
- Free-form text is correctly split into the three standup fields
- "skip" response is stored and excluded from the summary
- Responses after the window close are accepted and marked `is_late = true`
- Duplicate responses (user submits twice) update, not insert

**Notes:** Parser does not need to handle structured Block Kit responses in this phase (that is a P1 feature in Phase 2).

---

## Phase 2: Summary Generation and Posting

### Item 2.1 — Summary Aggregator

<!-- STATUS:todo -->

**Status:** todo
**Size:** S
**Files:** `src/summary/aggregator.ts`, `src/db/summaryRepository.ts`

**Tasks:**
- [ ] Query all responses for a workspace for the current date at summary time
- [ ] Calculate participation rate: (responses + skips) / roster_count
- [ ] Identify non-respondents: roster members with no response record
- [ ] Separate blocker entries for highlighted display
- [ ] Write summary record to `summaries` table

**Acceptance Criteria:**
- Participation rate calculation matches formula in PRD (responses / roster_count)
- Non-respondents are included in summary as "No response"
- Summary is idempotent: running aggregation twice produces the same result
- Unit tests cover edge cases: all responded, none responded, all skipped

---

### Item 2.2 — Summary Slack Post

<!-- STATUS:todo -->

**Status:** todo
**Size:** M
**Files:** `src/summary/slackFormatter.ts`, `src/scheduler/summaryJob.ts`

**Tasks:**
- [ ] Build Slack Block Kit summary message layout
- [ ] List each team member's response alphabetically
- [ ] Highlight blocker entries with warning emoji and bold text
- [ ] @mention team lead if any blockers exist
- [ ] Include participation rate line (e.g., "8/10 responded")
- [ ] Post to configured summary channel
- [ ] Retry up to 3 times on post failure; DM admin on final failure

**Acceptance Criteria:**
- Summary posts to the correct channel within 30 seconds of 10:00 AM
- Blockers are visually distinct from non-blocker entries
- Team lead is @mentioned when has_blocker is true
- Retry logic fires and admin DM is sent on repeated failure

---

## Notes

- Phase 3 (Configuration API) and Phase 4 (Reporting) are in scope for v2 and are not in this plan
- All items should be implemented on a feature branch; create a PR per item
- After Phase 2 is complete, run end-to-end test with a real Slack workspace before declaring MVP done
