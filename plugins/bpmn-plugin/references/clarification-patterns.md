# Clarification Question Patterns

This document contains question templates for gathering process requirements before generating BPMN XML.

---

## Question Format Template

Every question must follow this exact format:

```
## Question [N]: [Topic Category]

[Clear, specific question text]

### Options:

**A) [Recommended]**: [Specific answer]
   *Why*: [2-3 sentence reasoning for why this is the best choice based on the process description and BPMN best practices]

**B)** [Alternative answer 1]
**C)** [Alternative answer 2]
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions (auto-accept mode)

---
Your choice (A/B/C/D/E):
```

---

## Phase 1: Process Scope Questions

### Q1: Process Name

```
## Question 1: Process Name

What should this process be called? This name will be used as the process identifier and displayed in BPMN tools.

### Options:

**A) [Recommended]**: [Inferred name from description]
   *Why*: This name clearly describes the process purpose and follows the naming convention of [Verb] + [Noun] which is standard for BPMN processes.

**B)** [Shorter alternative]
**C)** [More detailed alternative]
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions

---
Your choice (A/B/C/D/E):
```

### Q2: Process Trigger (Start Event)

```
## Question 2: Process Trigger

What initiates this process? The answer determines what type of start event to use.

### Options:

**A) [Recommended]**: [Event type] - [Description]
   *Why*: Based on "[trigger phrase from description]", this process appears to be initiated by [reasoning]. A [event type] start event accurately models this trigger.

**B)** None Start Event - Process is started manually or trigger is unspecified
**C)** Timer Start Event - Process runs on a schedule (daily, weekly, etc.)
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions

---
Your choice (A/B/C/D/E):
```

**Start Event Recommendations by Context:**

| Description Keywords | Recommended Start Event | Reasoning |
|---------------------|------------------------|-----------|
| "customer submits", "request received", "order placed" | Message Start | External trigger from another party |
| "every day", "weekly", "at midnight", "scheduled" | Timer Start | Time-based trigger |
| "when inventory low", "if condition met" | Conditional Start | Data condition trigger |
| "alert broadcast", "signal received" | Signal Start | Broadcast event trigger |
| No specific trigger mentioned | None Start | Manual or undefined trigger |

### Q3: Process Completion (End Events)

```
## Question 3: Process Completion

How does this process end? Processes can have multiple end states (success, failure, cancellation, etc.).

### Options:

**A) [Recommended]**: [Number] end state(s): [List of end states]
   *Why*: Based on the process flow, [reasoning for end states]. These end events cover the expected outcomes.

**B)** Single end state - [Description]
**C)** Multiple end states - Success and Error only
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions

---
Your choice (A/B/C/D/E):
```

**End Event Recommendations:**

| Scenario | End Events | Types |
|----------|-----------|-------|
| Simple linear process | 1 | None End |
| Process with validation | 2 | None End (success), Error End (failure) |
| Process with cancellation | 2-3 | None End, Error End, Message End (cancelled) |
| Complex branching | Multiple | Based on distinct outcomes |

---

## Phase 2: Participant Questions

### Q4: Process Scope

```
## Question 4: Process Scope

Is this a single-participant process or does it involve multiple organizations/systems communicating?

### Options:

**A) [Recommended]**: Single process (one pool)
   *Why*: The described process appears to occur within a single organization/system boundary. All activities are performed by internal actors without external message exchanges.

**B)** Collaboration (multiple pools) - [Identified participants]
**C)** Single process with lanes (multiple roles within one organization)
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions

---
Your choice (A/B/C/D/E):
```

### Q5: Roles/Lanes

```
## Question 5: Roles and Responsibilities

Should the process be divided into lanes representing different roles or departments?

### Options:

**A) [Recommended]**: [Yes/No] - [Reasoning]
   *Why*: [Explanation based on whether distinct roles were mentioned]

**B)** No lanes - All tasks performed by same role/system
**C)** [Number] lanes: [List of identified roles]
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions

---
Your choice (A/B/C/D/E):
```

---

## Phase 3: Activity Questions

### Q6: Main Activities

```
## Question 6: Main Activities

What are the primary steps/tasks in this process? List them in sequential order.

### Options:

**A) [Recommended]**: [Numbered list of activities]
   *Why*: These activities represent the core workflow extracted from the description. Each step is atomic and represents a distinct unit of work.

**B)** Simplified: [Fewer, more consolidated activities]
**C)** Detailed: [More granular activities]
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions

---
Your choice (A/B/C/D/E):
```

### Q7: Task Types

```
## Question 7: Task Types

For each activity, what type of task best represents how the work is performed?

### Options:

**A) [Recommended]**:
   - [Task 1]: [Task Type] - [Reason]
   - [Task 2]: [Task Type] - [Reason]
   - [etc.]
   *Why*: Task types are assigned based on who/what performs the work and how it's executed.

**B)** All User Tasks (human-performed)
**C)** All Service Tasks (system-automated)
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions

---
Your choice (A/B/C/D/E):
```

**Task Type Assignment Guide:**

| Indicator in Description | Task Type |
|-------------------------|-----------|
| "user", "person", "employee", "reviewer", "approver" | User Task |
| "system", "API", "service", "automated", "integration" | Service Task |
| "calculate", "transform", "script", "code" | Script Task |
| "send email", "notify", "send message" | Send Task |
| "wait for", "receive", "expect response" | Receive Task |
| "business rule", "decision", "policy" | Business Rule Task |
| "physical", "manual", "hands-on" | Manual Task |

### Q8: Task Sequencing

```
## Question 8: Task Sequencing

Are there any activities that can happen in parallel, or must all tasks be sequential?

### Options:

**A) [Recommended]**: [Sequential/Parallel description]
   *Why*: [Reasoning based on task dependencies]

**B)** Strictly sequential - each task depends on the previous
**C)** Multiple parallel branches: [Description]
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions

---
Your choice (A/B/C/D/E):
```

### Q9: Task Descriptions (CRITICAL FOR POWERPOINT)

**This question is essential for generating rich content in PowerPoint presentations.**

```
## Question 9: Task Descriptions

For each task, I'll generate a detailed description explaining what happens during this step. These descriptions will be used for:
- PowerPoint presentation bullet points (Level 3 detail)
- Process documentation
- Training materials

Here are the proposed descriptions. Would you like to modify any?

### Proposed Task Descriptions:

| Task | Description |
|------|-------------|
| [Task 1 Name] | [2-3 sentence description covering purpose, actions, actor, and completion criteria] |
| [Task 2 Name] | [2-3 sentence description covering purpose, actions, actor, and completion criteria] |
| ... | ... |

### Options:

**A) [Recommended]**: Use these descriptions as-is
   *Why*: These descriptions capture the essential information needed for documentation and provide appropriate detail for presentations.

**B)** More concise - reduce to 1 sentence each
**C)** More detailed - expand to 4-5 sentences each
**D)** Let me provide custom descriptions for specific tasks
**E)** Accept recommended answers for all remaining questions

---
Your choice (A/B/C/D/E):
```

**Description Generation Guidelines:**

When generating task descriptions, include:

1. **Action verb** - What specifically happens (validates, reviews, calculates, sends)
2. **Actor/System** - Who or what performs it (system, reviewer, manager, API)
3. **Inputs** - What data or documents are used
4. **Outputs** - What is produced or changed
5. **Success criteria** - How completion is determined

**Examples by Task Type:**

| Task Type | Example Description |
|-----------|---------------------|
| User Task | "Reviewer examines the submitted application for completeness and accuracy. Verifies all required documents are attached and applicant information matches supporting documentation. Marks application as approved, rejected, or requires additional information." |
| Service Task | "System validates order details including product availability, pricing accuracy, and customer information. Checks for duplicate orders and verifies shipping address is within serviceable region. Returns validation status with any error codes." |
| Send Task | "System sends automated email notification to relevant stakeholders. Includes summary of completed action, any required next steps, and links to detailed information. Logs notification delivery status for audit purposes." |
| Manual Task | "Warehouse staff physically inspects items for damage before packaging. Verifies item quantity and condition against pick list. Flags any issues for supervisor review before proceeding." |
| Script Task | "Script calculates applicable discounts based on customer tier, order value, and active promotions. Applies discount rules in priority order and stores final percentage. Logs calculation details for transparency." |

### Q10: Subprocesses

```
## Question 10: Subprocess Candidates

Should any group of activities be encapsulated as a subprocess?

### Options:

**A) [Recommended]**: [Yes/No] - [Reasoning]
   *Why*: [Explanation of subprocess benefits or why not needed]

**B)** No subprocesses - keep flat structure
**C)** Create subprocess for: [Group of activities]
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions

---
Your choice (A/B/C/D/E):
```

**Subprocess Indicators:**
- Group of tasks that are logically related
- Activities that might need separate error handling
- Reusable process segments
- Complex sections that benefit from visual grouping

---

## Phase 4: Flow Control Questions

### Q11: Decision Points

```
## Question 10: Decision Points

Are there points in the process where different paths are taken based on conditions?

### Options:

**A) [Recommended]**: Yes - [Number] decision point(s):
   - [Decision 1]: [Condition description]
   - [Decision 2]: [Condition description]
   *Why*: These decision points represent where the process flow diverges based on data or outcomes.

**B)** No decision points - linear flow
**C)** Single decision point: [Description]
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions

---
Your choice (A/B/C/D/E):
```

### Q12: Gateway Types

```
## Question 11: Gateway Types

For each decision point, what type of gateway should be used?

### Options:

**A) [Recommended]**:
   - [Decision 1]: Exclusive Gateway (XOR) - only one path taken
   - [Decision 2]: Parallel Gateway (AND) - all paths taken
   *Why*: Gateway types are selected based on how many outgoing paths are activated.

**B)** All Exclusive Gateways (one path based on condition)
**C)** Mix of gateway types: [Specific assignments]
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions

---
Your choice (A/B/C/D/E):
```

### Q13: Default Flows

```
## Question 12: Default Flows

For exclusive/inclusive gateways, which path should be the default (taken when no conditions match)?

### Options:

**A) [Recommended]**: [Default path description]
   *Why*: This path represents the most common or safest outcome when no explicit condition is matched.

**B)** [Alternative default]
**C)** No default - all paths have explicit conditions
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions

---
Your choice (A/B/C/D/E):
```

### Q14: Loops/Cycles

```
## Question 13: Loops and Cycles

Are there any repeating patterns or loops in this process?

### Options:

**A) [Recommended]**: [Yes/No] - [Description]
   *Why*: [Reasoning based on process description]

**B)** No loops - process flows in one direction
**C)** Loop: [Description of repeating section]
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions

---
Your choice (A/B/C/D/E):
```

---

## Phase 5: Events & Exceptions Questions

### Q15: Intermediate Events

```
## Question 14: Intermediate Events

Are there any waiting points, messages sent/received, or time delays during the process?

### Options:

**A) [Recommended]**: [Yes/No] - [List of intermediate events]
   *Why*: [Reasoning based on process description]

**B)** No intermediate events
**C)** Timer events only: [Wait periods]
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions

---
Your choice (A/B/C/D/E):
```

### Q16: Boundary Events

```
## Question 15: Boundary Events

Should any tasks have boundary events for timeouts, errors, or external interrupts?

### Options:

**A) [Recommended]**: [Yes/No] - [List of boundary events]
   *Why*: [Reasoning for timeout/error handling needs]

**B)** No boundary events needed
**C)** Timeout boundaries on: [Tasks]
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions

---
Your choice (A/B/C/D/E):
```

**Boundary Event Recommendations:**

| Scenario | Boundary Event Type |
|----------|-------------------|
| Task has SLA/deadline | Timer (interrupting) |
| Need periodic reminders | Timer (non-interrupting) |
| Task can fail with error | Error |
| Task can be cancelled externally | Message |
| Task can receive updates | Signal (non-interrupting) |

### Q17: Error Handling

```
## Question 16: Error Handling

How should errors be handled in this process?

### Options:

**A) [Recommended]**: [Error handling strategy]
   *Why*: [Reasoning based on process criticality and error scenarios]

**B)** Simple - end process on error
**C)** Retry logic with eventual failure path
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions

---
Your choice (A/B/C/D/E):
```

### Q18: Compensation

```
## Question 17: Compensation

If the process fails partway through, should previous steps be undone (compensation)?

### Options:

**A) [Recommended]**: [Yes/No] - [Reasoning]
   *Why*: [Explanation based on process nature]

**B)** No compensation needed
**C)** Compensation required for: [Specific tasks]
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions

---
Your choice (A/B/C/D/E):
```

---

## Phase 6: Data & Integration Questions

### Q19: Data Objects

```
## Question 18: Data Objects

What data is passed between activities in this process?

### Options:

**A) [Recommended]**: [List of data objects]
   *Why*: These data objects represent the key information flowing through the process.

**B)** No explicit data objects needed
**C)** Single data object: [Primary entity]
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions

---
Your choice (A/B/C/D/E):
```

### Q20: External Systems

```
## Question 19: External Systems

Does this process integrate with external systems or services?

### Options:

**A) [Recommended]**: [Yes/No] - [List of integrations]
   *Why*: [Reasoning based on process description]

**B)** No external integrations
**C)** [Specific integrations]
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions

---
Your choice (A/B/C/D/E):
```

### Q21: Message Flows (for Collaborations)

```
## Question 20: Message Flows

[Only if collaboration was selected in Q4]

What messages are exchanged between participants?

### Options:

**A) [Recommended]**: [List of message flows]
   *Why*: These messages represent the communication between pools.

**B)** [Alternative message structure]
**C)** [Simplified message flows]
**D)** Provide your own answer
**E)** Accept recommended answers for all remaining questions

---
Your choice (A/B/C/D/E):
```

---

## Phase 7: Optimization Review

### Q22: Final Structure Review

```
## Question 21: Final Structure Review

Based on your answers, here is the proposed process structure. Would you like to make any adjustments?

**Proposed Structure:**
```
[ASCII diagram or structured summary of process]
```

**Elements:**
- Start: [Start event type]
- Tasks: [Count] ([types])
- Gateways: [Count] ([types])
- End: [End event types]

### Options:

**A) [Recommended]**: Proceed with this structure
   *Why*: This structure accurately represents the described process with appropriate BPMN elements.

**B)** Simplify - reduce number of elements
**C)** Add more detail - [Specific additions]
**D)** Provide your own answer
**E)** Accept recommended answer and generate XML

---
Your choice (A/B/C/D/E):
```

---

## Adaptive Question Logic

### Skip Conditions

Skip questions based on previous answers:

| If... | Skip Questions |
|-------|---------------|
| Single pool selected (Q4) | Q20 (Message Flows) |
| No decision points (Q10) | Q11, Q12 (Gateway types, defaults) |
| Simple linear process | Q13 (Loops), Q9 (Subprocesses) |
| No intermediate events (Q14) | Detailed event questions |
| No errors mentioned | Q16, Q17 (Error handling, compensation) |

### Always Ask

These questions should always be asked:
- Q1: Process Name
- Q2: Start Event
- Q3: End Events
- Q6: Main Activities
- Q9: Task Descriptions (CRITICAL for PowerPoint generation)
- Q22: Final Review

### Question Depth by Complexity

**Simple Process (< 5 tasks, no decisions):**
- Ask Q1-Q3, Q6, Q7, Q9, Q22
- Skip gateway, subprocess, event questions

**Medium Process (5-10 tasks, 1-2 decisions):**
- Ask most questions
- Skip collaboration, compensation questions if not relevant

**Complex Process (> 10 tasks, multiple decisions, parallel flows):**
- Ask all applicable questions
- Consider breaking into multiple processes

---

## Auto-Accept Mode Behavior

When user selects **E) Accept recommended answers**:

1. Store flag: `AUTO_ACCEPT_MODE = true`
2. For each remaining question:
   - Automatically select option A
   - Log the decision: `Q[N]: [Topic] → [Recommended Answer]`
3. Continue to next question without prompting
4. Before generating XML, display summary:

```
## Auto-Accepted Decisions Summary

The following decisions were automatically accepted:

| Question | Topic | Decision |
|----------|-------|----------|
| Q[N] | [Topic] | [Answer] |
| ... | ... | ... |

Proceeding with XML generation using these decisions.
```

5. Generate XML with all accumulated decisions
