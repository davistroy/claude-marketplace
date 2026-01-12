# Conversion Notes: Social Media Community Management

## Source Document

**File:** `examples/Current_State_Business_Process_Social_Media_Community_Management.md`

## Extraction Summary

### Process Identification

| Attribute | Extracted Value | Source |
|-----------|-----------------|--------|
| Process Name | Social Media Community Management | H1: "Current State Business Process: Social Media Community Management" |
| Process ID | `CommunityManagement` | Sanitized from name |
| Version | 1.1 | Frontmatter "Document Version" |
| Status | Current State | Frontmatter "Status" |

### Phase Mapping

| Document Section | Phase Name | Phase Comment |
|------------------|------------|---------------|
| 3.1 Step 1: Monitor and Intake | Monitor and Intake | `<!-- Phase 1: Monitor and Intake -->` |
| 3.2 Step 2: Review and Triage | Review and Triage | `<!-- Phase 2: Review and Triage -->` |
| 3.3 Step 3: Routing and Ownership | Routing and Ownership | `<!-- Phase 3: Routing and Ownership -->` |
| 3.4 Step 4: Response Development and Approval | Response Development | `<!-- Phase 4: Response Development and Approval -->` |
| 3.5 Step 5: Publish and/or Escalate | Publish and Escalate | `<!-- Phase 5: Publish and Escalate -->` |
| 3.6 Step 6: Resolve and Close the Loop | Resolve and Close | `<!-- Phase 6: Resolve and Close -->` |
| 3.7 Step 7: Report and Review | Report and Review | `<!-- Phase 7: Report and Review -->` |

### Role Extraction

| Document Role | Lane Name | Color Mapping | Source Pattern |
|---------------|-----------|---------------|----------------|
| Community Manager | Community Manager | `#dae8fc` / `#6c8ebf` | "Roles Involved" sections |
| Social Team Lead | Social Team Lead | `#dae8fc` / `#6c8ebf` | "Roles Involved" sections |
| Customer Care | Customer Care | `#f5f5f5` / `#666666` | Section 6, routing table |
| Store Manager/Franchisee | Field Operations | `#ffe6cc` / `#d79b00` | Section 6, routing table |
| Social Analytics/Insights | Analytics | `#e1d5e7` / `#9673a6` | Section 7 |
| Customer | Customer (External Pool) | `#f5f5f5` / `#666666` | Implied external party |

### Task Extraction

| Section | Task Name | Task Type | Rationale |
|---------|-----------|-----------|-----------|
| 3.1 | Monitor and Intake | User Task | "manually review", human-driven |
| 3.2 | Review and Triage | User Task | "manually review" explicitly stated |
| 3.3 | (Gateway) Route by Category | XOR Gateway | Routing table with multiple destinations |
| 3.4 | Draft Response | User Task | "drafts response" - human activity |
| 3.4 | Review and Approve Response | User Task | Approval workflow |
| 3.5 | Publish Public Response | Send Task | "Posted as a reply" - sending message |
| 3.5 | Send Private Follow-up | Send Task | "Direct message" - sending message |
| 3.6 | Close the Loop | User Task | "follows up with customer" |
| 3.6 | Handle Service Recovery | User Task | Customer Care escalation |
| 3.6 | Investigate Location Issue | User Task | Store manager investigation |
| 3.6 | Implement Corrective Action | User Task | Store manager action |
| 3.7 | Compile Performance Report | User Task | Manual spreadsheet work described |
| 3.7 | Identify Trends | User Task | Review trends for improvement |

### Gateway Identification

| Document Pattern | Gateway Type | Condition Expression |
|------------------|--------------|----------------------|
| Routing Destinations table (3.3) | Exclusive (XOR) | `${category == '...'}`  |
| Approval Requirements table (3.4) | Exclusive (XOR) | `${sensitivityLevel == '...'}`  |

### Event Identification

| Document Pattern | Event Type | BPMN Element |
|------------------|------------|--------------|
| "Social channels are monitored" | Message Start | `<bpmn:startEvent><bpmn:messageEventDefinition/>` |
| End of reporting cycle | None End | `<bpmn:endEvent>` |

### Documentation Extraction Examples

**Example 1: Monitor and Intake**

Source markdown:
```markdown
### 3.1 Step 1: Monitor and Intake

**Roles Involved:**
- Community Manager
- Social Listening Analyst

**Process Description:**

Social channels and location pages are monitored using enterprise social
management and listening tools. Incoming interactions are collected into
a central inbox for review.

**Platforms Monitored:**
- Twitter/X
- Instagram
- Facebook
- Location-specific social media pages
```

Extracted documentation:
```xml
<bpmn:documentation>
    Community Manager and Social Listening Analyst monitor social channels
    and location pages using enterprise social management and listening tools
    (e.g., Sprout Social, Hootsuite, Brandwatch). Platforms monitored include
    Twitter/X, Instagram, Facebook, and location-specific social media pages.
    ...
</bpmn:documentation>
```

**Example 2: Review and Triage**

Source markdown (tables + bullets merged):
```markdown
| Criterion | Assessment |
|-----------|------------|
| **Topic/Intent** | Question, complaint, praise, general engagement |
| **Location Relevance** | Store-level issue vs. enterprise/brand-level |
...

**Categorization Buckets:**
1. **Location-specific service issues**
2. **Digital/loyalty-related inquiries**
3. **Brand/marketing questions**
...
```

Merged into comprehensive documentation including criteria table data and categorization list.

## Multi-Pool Structure

The document mentions "Customer" interactions repeatedly:
- "customer posts on social media"
- "Notify Customer"
- "Customer receives notification"

This triggered creation of a collapsed Customer pool with message flows:
- `MessageFlow_CustomerPost`: Customer → StartEvent
- `MessageFlow_PublicResponse`: PublishTask → Customer
- `MessageFlow_PrivateMessage`: PrivateFollowup → Customer
- `MessageFlow_Resolution`: CloseLoop → Customer

## Assumptions Made

1. **Workflow is linear-dominant**: The 7 steps execute mostly sequentially with escalation branches
2. **Escalation paths return to main flow**: Service recovery and location issues feed back into response drafting
3. **Reporting is periodic, not per-interaction**: Report phase triggers after interaction resolution cycle
4. **External routing destinations simplified**: Legal, PR, Digital Support routes not fully modeled as lanes (mentioned as routing targets but no detailed activities provided)

## Validation Results

- All elements connected via sequence flows
- All tasks have documentation
- All gateways have labeled conditions
- Message flows connect to external pool
- Layout follows Draw.io standards (lane heights, element spacing)
- Phase comments included for PowerPoint generation compatibility
