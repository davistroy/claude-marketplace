# Markdown Parsing Guide for BPMN Conversion

## Overview

This guide provides detailed patterns for extracting BPMN elements from various markdown document structures commonly used in business process documentation.

## Document Structure Recognition

### Process Title Extraction

**Priority Order:**

1. **YAML Frontmatter:**
```markdown
---
title: Social Media Community Management
process_name: Community Management Workflow
---
```

2. **First H1 Heading:**
```markdown
# Current State Business Process: Social Media Community Management
```
Extract: "Social Media Community Management" (remove prefix like "Current State Business Process:")

3. **First Non-Empty H2 if No H1:**
```markdown
## Social Media Community Management Process
```

### Version and Metadata Extraction

```markdown
**Document Version:** 1.1
**Date:** January 12, 2026
**Status:** Draft | In Review | Approved | Current State | Future State
```

Map to BPMN definitions metadata or XML comments.

## Phase/Stage Detection Patterns

### Pattern 1: Explicit Step Numbering

```markdown
### 3.1 Step 1: Monitor and Intake
### 3.2 Step 2: Review and Triage
### 3.3 Step 3: Routing and Ownership
```

**Regex:** `^#{2,4}\s*[\d.]*\s*Step\s+\d+[:.]?\s*(.+)$`

**Extraction:** Phase name from capture group 1

### Pattern 2: Phase/Stage Keywords

```markdown
## Phase 1: Intake and Validation
## Stage 2: Processing
## Step 3: Fulfillment
```

**Regex:** `^#{2,3}\s*(Phase|Stage|Step)\s+\d+[:.]?\s*(.+)$`

### Pattern 3: Numbered Workflow Sections

```markdown
## 3. Current State Workflow
### 3.1 Monitor and Intake
### 3.2 Review and Triage
```

**Regex:** `^#{2,4}\s*([\d.]+)\s+(.+)$`

Sequential numbering indicates phase progression.

### Pattern 4: ASCII Workflow Diagram

```markdown
┌─────────────────────────────────────────────────────────────────────────┐
│                    COMMUNITY MANAGEMENT WORKFLOW                         │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────────┐  │
│  │ STEP 1   │───▶│ STEP 2   │───▶│ STEP 3   │───▶│ STEP 4           │  │
│  │ Monitor  │    │ Review & │    │ Routing/ │    │ Response Dev &   │  │
│  │ & Intake │    │ Triage   │    │ Ownership│    │ Approval         │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────────────┘  │
```

**Parsing Strategy:**
1. Detect box boundaries: `┌`, `└`, `┐`, `┘`
2. Extract labels between `│` characters
3. Map arrows (`───▶`, `─▶`, `→`) to sequence flows
4. First line in box = step ID, remaining lines = name

## Role/Actor Detection Patterns

### Pattern 1: Explicit Role Sections

```markdown
**Roles Involved:**
- Community Manager
- Social Team Lead

**Actors:**
- Finance Department
- Legal Team
```

**Regex for header:** `^\*\*(Roles?|Actors?)\s*(Involved|Responsible)?:?\*\*`

**Extraction:** List items following the header

### Pattern 2: Role Tables

```markdown
| Role | Primary Responsibilities |
|------|-------------------------|
| **Community Manager** | Monitor channels, triage interactions |
| **Social Team Lead** | Oversee decisions, manage escalations |
```

**Parsing:**
1. Find tables with "Role" column
2. Extract role names from first column
3. Use responsibilities as task documentation

### Pattern 3: Inline Role Mentions

```markdown
The **Community Manager** reviews incoming interactions...
```

**Regex:** `\*\*([A-Z][A-Za-z\s/]+)\*\*\s+(reviews?|performs?|handles?|manages?|executes?)`

### Pattern 4: Organizational Structure Sections

```markdown
## 2.1 Organizational Structure

**Central/Corporate Level:**
- Establishes brand standards
- Creates governance policies

**Regional/Local Level:**
- Regional teams handle engagement
- Execute within guidelines
```

Creates hierarchy of lanes or pools.

## Task Detection Patterns

### Pattern 1: Bold Action Headers

```markdown
**Process Description:**

Community managers manually review inbound interactions to assess and categorize them.
```

The paragraph following becomes task documentation.

### Pattern 2: Numbered Sub-Steps

```markdown
1. **Public acknowledgment** - Brief public response expressing concern
2. **Private follow-up** - Direct message to gather details
3. **Resolution and close** - Thank customer and confirm resolution
```

Each creates a separate task with the bold text as name and description after dash as documentation.

### Pattern 3: Task Tables

```markdown
| Task | Owner | Description |
|------|-------|-------------|
| Validate Order | System | Check order details and pricing |
| Review Request | Manager | Approve or reject based on policy |
```

### Pattern 4: Action Verbs in Headings

```markdown
### Review and Triage Interactions
### Route to Appropriate Team
### Develop and Approve Response
```

Headings with action verbs become tasks.

## Gateway Detection Patterns

### Pattern 1: Decision Tables

```markdown
| Criterion | Assessment |
|-----------|------------|
| **Topic/Intent** | Question, complaint, praise |
| **Urgency** | High, Medium, Low |
| **Risk Level** | Critical, Standard |
```

Multiple assessment categories often indicate XOR gateway branches.

### Pattern 2: Routing Tables

```markdown
| Route | Scenario |
|-------|----------|
| Corporate Team | Brand-level questions |
| Customer Care | Service recovery |
| Legal | Liability concerns |
```

Each route becomes a gateway outgoing path.

### Pattern 3: Conditional Language

```markdown
Based on triage results, the interaction is routed to:
- If brand question → Corporate Social Team
- If service issue → Customer Care
- If legal concern → Legal Department
```

### Pattern 4: Decision Questions

```markdown
**Credit Check Result?**
- Approved → Continue to billing
- Requires CFO Approval → Escalate
- Declined → Request prepayment
```

Question followed by options = XOR gateway.

### Pattern 5: Parallel Processing

```markdown
After contract signing, three parallel tracks begin:
1. Legal review
2. Finance setup
3. Security assessment

All tracks must complete before implementation begins.
```

"parallel tracks" + "all must complete" = AND split + AND join

## Event Detection Patterns

### Pattern 1: Process Triggers

```markdown
The process **begins when** a customer posts on social media.
The workflow is **triggered by** receiving a signed contract.
Process **initiates** upon order placement.
```

**Regex:** `(begins?\s+when|triggered\s+by|initiates?\s+(upon|when)|starts?\s+with)`

### Pattern 2: Timer Events

```markdown
Wait **30 days** after launch before health check.
After a **5-day** waiting period, follow up.
```

**Regex:** `(wait|after)\s+\*?\*?(\d+)\s*(days?|hours?|minutes?)\*?\*?`

### Pattern 3: Message Events

```markdown
Await customer response to questionnaire.
Wait for signed agreement from legal.
Receive payment confirmation.
```

Keywords: await, wait for, receive, expect

### Pattern 4: Process Completion

```markdown
The process **completes when** the customer is in steady state.
Workflow **ends with** successful onboarding.
```

## Documentation Extraction

### Best Practices

1. **Capture Full Context:**
   - Include the paragraph immediately following a task heading
   - Capture all bullet points under a task description
   - Include relevant table data

2. **Synthesize from Multiple Sources:**
   ```markdown
   ### Monitor and Intake

   **Roles:** Community Manager

   Social channels are monitored using enterprise tools.

   **Platforms:**
   - Twitter/X
   - Instagram
   - Facebook
   ```

   Combine into comprehensive documentation:
   ```
   Community Manager monitors social channels using enterprise social
   management tools. Platforms monitored include Twitter/X, Instagram,
   and Facebook. Incoming interactions are collected for review.
   ```

3. **Preserve Key Details:**
   - Tool names mentioned (Hootsuite, Salesforce, etc.)
   - Metrics and SLAs
   - Specific criteria and rules

### Documentation Template

```xml
<bpmn:documentation>
    [ACTOR] [ACTION_VERB] [OBJECT]. [ADDITIONAL_CONTEXT].
    [CRITERIA_OR_RULES]. [TOOLS_USED]. [EXPECTED_OUTCOME].
</bpmn:documentation>
```

## Flow Inference

### Sequential Flow Detection

When tasks are numbered or ordered in document:
```markdown
1. Review request
2. Check inventory
3. Process payment
4. Ship order
```

Create sequence flows: Review → Inventory → Payment → Ship

### Branching Flow Detection

When multiple outcomes listed:
```markdown
After review:
- **Approved**: Proceed to implementation
- **Rejected**: Return to requester
- **Needs Info**: Request clarification
```

Create XOR gateway with three outgoing flows.

### Loop Detection

```markdown
If issues are found, remediate and **return to** review step.
Process repeats until all items are validated.
```

Keywords: return to, repeats, loop back, cycle

## Special Sections

### Known Issues / Pain Points

```markdown
### 5.1 Response Timeliness
- Approval dependencies extend response times
- Manual triage creates bottlenecks
```

These may inform:
- Error boundary events
- Escalation paths
- Process improvement annotations

### Technology/Tools Sections

```markdown
### 7.1 Current Tools
| Tool Category | Examples |
|---------------|----------|
| Social Management | Sprout Social, Hootsuite |
| CRM | Salesforce, Zendesk |
```

Use for:
- Service task implementation hints
- System integration annotations
- Lane naming (e.g., "Hootsuite" → "Social Platform")

### Metrics / SLAs

```markdown
| Metric | Target |
|--------|--------|
| Response Time | < 4 hours |
| Resolution Time | < 24 hours |
```

Use for:
- Timer event durations
- Boundary event timeouts
- Documentation enrichment

## Edge Cases

### Ambiguous Role Assignments

When a task mentions multiple roles without clarity:
```markdown
The Social Team Lead and Legal review the response.
```

**Strategy:** Assign to first mentioned role; note collaboration in documentation.

### Nested Subprocesses

```markdown
#### Data Migration Process
1. Assign specialist
2. Profile data
3. Develop scripts
4. Test migration
5. Execute migration
```

If section is clearly a sub-workflow, create `<bpmn:subProcess>` with internal elements.

### External Actor Interactions

```markdown
Customer receives notification and responds with confirmation.
```

If document tracks external party actions, consider:
- External pool with placeholder activities
- Message flows between pools
- Receive/send tasks for interactions
