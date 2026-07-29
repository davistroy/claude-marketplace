# Clarification Question Patterns

This document contains question templates for gathering process requirements before generating BPMN XML.

---

## Question Format Template

Every question is asked with the native `AskUserQuestion` tool — never a hand-rolled
lettered menu. Each question follows this exact shape:

```json
{
  "questions": [
    {
      "question": "[Clear, specific question text ending in a question mark]",
      "header": "[≤12 chars]",
      "multiSelect": false,
      "options": [
        {
          "label": "[Best answer] (Recommended)",
          "description": "[Why this is the best choice for this process, per BPMN practice]"
        },
        {
          "label": "[Alternative 1]",
          "description": "[What choosing this means]"
        },
        {
          "label": "[Alternative 2]",
          "description": "[What choosing this means]"
        }
      ]
    }
  ]
}
```

**Rules:**

- 2–4 options, real answers only. The recommended option goes first, with `(Recommended)` in its label.
- Never add a `Provide your own answer` or `None` option — the harness always supplies a free-text
  **Other** box and a **Skip** control. Adding them wastes a slot.
- `header` is the chip label, hard-capped at 12 characters.
- `multiSelect: true` only when the answers are genuinely not mutually exclusive.

**Auto-accept:** the old lettered format carried an `E) Accept recommended answers for all
remaining questions` slot on every question. That is now expressed through the free-text **Other**
box, which is available on every question and costs no option slot — see
[Auto-Accept Mode Behavior](#auto-accept-mode-behavior).

---

## Phase 1: Process Scope Questions

### Q1: Process Name

```json
{
  "questions": [
    {
      "question": "What should this process be called? (This name will be used as the process identifier.)",
      "header": "Process Name",
      "multiSelect": false,
      "options": [
        {
          "label": "Inferred name (Recommended)",
          "description": "Uses the name derived from the description; follows [Verb]+[Noun] BPMN convention"
        },
        {
          "label": "Shorter alternative",
          "description": "More concise version for simpler displays"
        },
        {
          "label": "More detailed alternative",
          "description": "Extended name with additional context"
        }
      ]
    }
  ]
}
```

### Q2: Process Trigger (Start Event)

```json
{
  "questions": [
    {
      "question": "What initiates this process? The answer determines what type of start event to use.",
      "header": "Start Event",
      "multiSelect": false,
      "options": [
        {
          "label": "Inferred trigger (Recommended)",
          "description": "Uses the trigger phrase from the description; selects the appropriate start event type"
        },
        {
          "label": "None Start Event",
          "description": "Process starts manually or trigger is unspecified"
        },
        {
          "label": "Timer Start Event",
          "description": "Process runs on a schedule (daily, weekly, at midnight, etc.)"
        },
        {
          "label": "Signal Start Event",
          "description": "Process is triggered by a broadcast or signal"
        }
      ]
    }
  ]
}
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

```json
{
  "questions": [
    {
      "question": "How does this process end? Processes can have multiple end states (success, failure, cancellation, etc.).",
      "header": "End Events",
      "multiSelect": false,
      "options": [
        {
          "label": "Inferred end states (Recommended)",
          "description": "Uses the process flow to determine end events; covers all expected outcomes"
        },
        {
          "label": "Single end state",
          "description": "Process ends in one way with a single None End event"
        },
        {
          "label": "Success and Error",
          "description": "Two end states: None End (success) and Error End (failure)"
        },
        {
          "label": "Multiple outcomes",
          "description": "Three+ end states for complex processes (success, error, cancellation, etc.)"
        }
      ]
    }
  ]
}
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

```json
{
  "questions": [
    {
      "question": "Is this a single-participant process or does it involve multiple organizations/systems communicating?",
      "header": "Scope",
      "multiSelect": false,
      "options": [
        {
          "label": "Single process (Recommended)",
          "description": "One pool; process occurs within a single organization/system boundary without external message exchanges"
        },
        {
          "label": "Collaboration",
          "description": "Multiple pools for different organizations/systems that exchange messages"
        },
        {
          "label": "Single with lanes",
          "description": "One pool with multiple lanes representing different roles/departments within one organization"
        }
      ]
    }
  ]
}
```

### Q5: Roles/Lanes

```json
{
  "questions": [
    {
      "question": "Should the process be divided into lanes representing different roles or departments?",
      "header": "Lanes",
      "multiSelect": false,
      "options": [
        {
          "label": "Inferred lanes (Recommended)",
          "description": "Based on distinct roles mentioned; organizes tasks by performer"
        },
        {
          "label": "No lanes",
          "description": "All tasks performed by the same role or system; flat structure"
        },
        {
          "label": "Multiple lanes",
          "description": "Divide process into separate lanes for identified roles or departments"
        }
      ]
    }
  ]
}
```

---

## Phase 3: Activity Questions

### Q6: Main Activities

```json
{
  "questions": [
    {
      "question": "What are the primary steps/tasks in this process? List them in sequential order.",
      "header": "Activities",
      "multiSelect": false,
      "options": [
        {
          "label": "Extracted activities (Recommended)",
          "description": "Core workflow from description; each step is atomic and distinct"
        },
        {
          "label": "Simplified",
          "description": "Fewer, consolidated activities for a higher-level view"
        },
        {
          "label": "Detailed",
          "description": "More granular activities for comprehensive documentation"
        }
      ]
    }
  ]
}
```

### Q7: Task Types

```json
{
  "questions": [
    {
      "question": "For each activity, what type of task best represents how the work is performed?",
      "header": "Task Types",
      "multiSelect": false,
      "options": [
        {
          "label": "Mixed task types (Recommended)",
          "description": "Assigns each task its appropriate type based on who performs it and how (User, Service, Script, Send, etc.)"
        },
        {
          "label": "All User Tasks",
          "description": "Every task is human-performed"
        },
        {
          "label": "All Service Tasks",
          "description": "Every task is system-automated"
        }
      ]
    }
  ]
}
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

```json
{
  "questions": [
    {
      "question": "Are there any activities that can happen in parallel, or must all tasks be sequential?",
      "header": "Sequencing",
      "multiSelect": false,
      "options": [
        {
          "label": "Inferred sequencing (Recommended)",
          "description": "Based on task dependencies; identifies parallel branches where tasks can run simultaneously"
        },
        {
          "label": "Strictly sequential",
          "description": "Each task depends on the previous; no parallel execution"
        },
        {
          "label": "Multiple parallel branches",
          "description": "Several independent branches that can execute concurrently"
        }
      ]
    }
  ]
}
```

### Q9: Task Descriptions (CRITICAL FOR POWERPOINT)

**This question is essential for generating rich content in PowerPoint presentations.**

```json
{
  "questions": [
    {
      "question": "For each task, here are proposed descriptions (2-3 sentences each, covering purpose, actions, actor, and completion criteria). Would you like to modify any?",
      "header": "Descriptions",
      "multiSelect": false,
      "options": [
        {
          "label": "Use as-is (Recommended)",
          "description": "Descriptions provide appropriate detail for both documentation and presentations"
        },
        {
          "label": "More concise",
          "description": "Reduce to 1 sentence per task for brevity"
        },
        {
          "label": "More detailed",
          "description": "Expand to 4-5 sentences for comprehensive documentation"
        }
      ]
    }
  ]
}
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

```json
{
  "questions": [
    {
      "question": "Should any group of activities be encapsulated as a subprocess?",
      "header": "Subprocesses",
      "multiSelect": false,
      "options": [
        {
          "label": "Inferred subprocesses (Recommended)",
          "description": "Groups logically-related tasks that benefit from encapsulation or reuse"
        },
        {
          "label": "No subprocesses",
          "description": "Keep a flat structure; no grouping needed"
        },
        {
          "label": "Multiple subprocesses",
          "description": "Create subprocesses for several distinct process segments"
        }
      ]
    }
  ]
}
```

**Subprocess Indicators:**
- Group of tasks that are logically related
- Activities that might need separate error handling
- Reusable process segments
- Complex sections that benefit from visual grouping

---

## Phase 4: Flow Control Questions

### Q11: Decision Points

```json
{
  "questions": [
    {
      "question": "Are there points in the process where different paths are taken based on conditions?",
      "header": "Decisions",
      "multiSelect": false,
      "options": [
        {
          "label": "Identified decision points (Recommended)",
          "description": "Process diverges based on data or outcomes; includes all decision branches"
        },
        {
          "label": "No decision points",
          "description": "Process flows linearly in one direction"
        },
        {
          "label": "Single decision point",
          "description": "One branch point where the process splits into multiple paths"
        }
      ]
    }
  ]
}
```

### Q12: Gateway Types

```json
{
  "questions": [
    {
      "question": "For each decision point, what type of gateway should be used?",
      "header": "Gateways",
      "multiSelect": false,
      "options": [
        {
          "label": "Mixed gateway types (Recommended)",
          "description": "Selects each gateway type based on how many outgoing paths are activated (Exclusive, Parallel, Inclusive)"
        },
        {
          "label": "All Exclusive Gateways",
          "description": "Only one path taken at each decision point based on conditions"
        },
        {
          "label": "Mixed with specification",
          "description": "Combination of gateway types; user specifies which for each decision"
        }
      ]
    }
  ]
}
```

### Q13: Default Flows

```json
{
  "questions": [
    {
      "question": "For exclusive/inclusive gateways, which path should be the default (taken when no conditions match)?",
      "header": "Defaults",
      "multiSelect": false,
      "options": [
        {
          "label": "Inferred default (Recommended)",
          "description": "Most common or safest outcome when no explicit condition matches"
        },
        {
          "label": "Alternative default",
          "description": "Specify a different default path"
        },
        {
          "label": "No default needed",
          "description": "All paths have explicit conditions; no default required"
        }
      ]
    }
  ]
}
```

### Q14: Loops/Cycles

```json
{
  "questions": [
    {
      "question": "Are there any repeating patterns or loops in this process?",
      "header": "Loops",
      "multiSelect": false,
      "options": [
        {
          "label": "Inferred loops (Recommended)",
          "description": "Based on process description; identifies repeating sections that need loop constructs"
        },
        {
          "label": "No loops",
          "description": "Process flows in one direction without repetition"
        },
        {
          "label": "Multiple loops",
          "description": "Several repeating patterns at different points"
        }
      ]
    }
  ]
}
```

---

## Phase 5: Events & Exceptions Questions

### Q15: Intermediate Events

```json
{
  "questions": [
    {
      "question": "Are there any waiting points, messages sent/received, or time delays during the process?",
      "header": "Int Events",
      "multiSelect": false,
      "options": [
        {
          "label": "Identified events (Recommended)",
          "description": "Based on process description; includes all intermediate events (timer, message, signal)"
        },
        {
          "label": "No intermediate events",
          "description": "Process has no waiting points or event handling"
        },
        {
          "label": "Timer events only",
          "description": "Only time delays; no message or signal events"
        }
      ]
    }
  ]
}
```

### Q16: Boundary Events

```json
{
  "questions": [
    {
      "question": "Should any tasks have boundary events for timeouts, errors, or external interrupts?",
      "header": "Boundary",
      "multiSelect": false,
      "options": [
        {
          "label": "Identified boundaries (Recommended)",
          "description": "Tasks with timeout/error/signal handling needs based on process requirements"
        },
        {
          "label": "No boundary events",
          "description": "No special error or timeout handling needed"
        },
        {
          "label": "Timeout only",
          "description": "Add timer boundary events for SLA enforcement"
        }
      ]
    }
  ]
}
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

```json
{
  "questions": [
    {
      "question": "How should errors be handled in this process?",
      "header": "Errors",
      "multiSelect": false,
      "options": [
        {
          "label": "Appropriate strategy (Recommended)",
          "description": "Based on process criticality; includes recovery, retry, or escalation paths"
        },
        {
          "label": "Simple - end on error",
          "description": "Process terminates when an error occurs"
        },
        {
          "label": "Retry with fallback",
          "description": "Attempt retries before falling back to error path"
        }
      ]
    }
  ]
}
```

### Q18: Compensation

```json
{
  "questions": [
    {
      "question": "If the process fails partway through, should previous steps be undone (compensation)?",
      "header": "Compensation",
      "multiSelect": false,
      "options": [
        {
          "label": "Inferred policy (Recommended)",
          "description": "Based on process nature; identifies tasks requiring compensation/rollback"
        },
        {
          "label": "No compensation",
          "description": "Partial completion is acceptable; no undo logic needed"
        },
        {
          "label": "Full compensation",
          "description": "All successfully-completed tasks must be undone on failure"
        }
      ]
    }
  ]
}
```

---

## Phase 6: Data & Integration Questions

### Q19: Data Objects

```json
{
  "questions": [
    {
      "question": "What data is passed between activities in this process?",
      "header": "Data Objects",
      "multiSelect": false,
      "options": [
        {
          "label": "Identified data (Recommended)",
          "description": "Key information flowing through process; represents primary entities and documents"
        },
        {
          "label": "No explicit objects",
          "description": "Data flow is implicit; no formal data object diagram needed"
        },
        {
          "label": "Single primary entity",
          "description": "One main data object flows through entire process"
        }
      ]
    }
  ]
}
```

### Q20: External Systems

```json
{
  "questions": [
    {
      "question": "Does this process integrate with external systems or services?",
      "header": "Integrations",
      "multiSelect": false,
      "options": [
        {
          "label": "Identified systems (Recommended)",
          "description": "Based on process description; lists all external integrations"
        },
        {
          "label": "No external integration",
          "description": "Process is entirely internal; no external system calls"
        },
        {
          "label": "Multiple integrations",
          "description": "Several external systems to be modeled"
        }
      ]
    }
  ]
}
```

### Q21: Message Flows (for Collaborations)

```json
{
  "questions": [
    {
      "question": "What messages are exchanged between participants? (Only applies if collaboration was selected in Q4.)",
      "header": "Messages",
      "multiSelect": false,
      "options": [
        {
          "label": "Identified messages (Recommended)",
          "description": "All communication between pools; includes message names and sequence"
        },
        {
          "label": "Simplified flows",
          "description": "High-level message structure; fewer details"
        },
        {
          "label": "Detailed specification",
          "description": "Comprehensive message definitions with data types and timing"
        }
      ]
    }
  ]
}
```

---

## Phase 7: Optimization Review

### Q22: Final Structure Review

```json
{
  "questions": [
    {
      "question": "Based on your answers, here is the proposed process structure. Would you like to make any adjustments?",
      "header": "Final Review",
      "multiSelect": false,
      "options": [
        {
          "label": "Proceed as-is (Recommended)",
          "description": "Structure accurately represents the process with appropriate BPMN elements"
        },
        {
          "label": "Simplify",
          "description": "Reduce number of elements for a higher-level view"
        },
        {
          "label": "Add more detail",
          "description": "Expand structure with additional elements or refinements"
        }
      ]
    }
  ]
}
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

There is no auto-accept *option* — offering one on every question would consume a slot on every
question. Instead, the user reaches it through the free-text **Other** box that `AskUserQuestion`
always supplies, at any point in the interview.

**Trigger:** an `Other` response expressing accept-all intent — "accept all", "use the recommended
answers", "auto-accept the rest", or similar. Treat the answer to the *current* question as the
recommended option as well, then:

1. Store flag: `AUTO_ACCEPT_MODE = true`
2. For each remaining question:
   - Automatically select the option labelled `(Recommended)` — do **not** issue an
     `AskUserQuestion` call for it
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
