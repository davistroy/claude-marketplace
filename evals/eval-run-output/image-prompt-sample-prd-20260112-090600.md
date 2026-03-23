# Image Generation Prompts: Daily Standup Bot

**Source:** sample-prd.md
**Generated:** 2026-01-12
**Default dimensions:** 11x17 (portrait, print/poster format)

---

## Prompt 1 — Hero Visual: The Async Standup Flow

**Best for:** product landing page, overview slide, conference presentation

**Prompt:**

A clean, modern infographic illustration showing an asynchronous daily standup workflow. On the left, a Slack chat interface displays a friendly bot icon sending three question cards to individual team members at 9:00 AM — the questions read "Yesterday:", "Today:", "Blockers:" in clean sans-serif type. Each team member (four diverse illustrated figures at laptops in different home office settings, one per time zone shown by small clock icons: PST, EST, CET, JST) types their response independently. A flowing arrow timeline moves left to right across the center of the image, labeled "9:00 AM → 9:45 AM collection window → 10:00 AM summary." On the right side, a Slack channel view shows a consolidated summary card in Slack Block Kit style — alphabetical list of team members with green checkmarks, one entry highlighted in amber with a warning icon labeled "Blocker" and an @mention tag. At the top of the image, a bold headline reads "Stand up without standing up." Color palette: Slack purple (#4A154B) and Salesforce blue accents on a light gray (#F8F8F8) background. Style: flat vector illustration, Slack brand-adjacent, suitable for a SaaS product marketing page. No photography. 11x17 inches portrait format, 300 DPI.

---

## Prompt 2 — Technical Architecture Diagram Style

**Best for:** engineering docs, README header, technical blog post

**Prompt:**

A technical architecture diagram rendered in an isometric flat illustration style showing the Daily Standup Bot system components. Four distinct boxes arranged in a processing pipeline from left to right: (1) "Slack Workspace" — illustrated as a purple Slack logo with DM notification bubbles floating upward; (2) "Bolt.js Message Handler" — a Node.js green hexagon icon inside a server rack silhouette labeled "ECS Fargate"; (3) "PostgreSQL Database" — a blue cylinder with tables labeled "responses" and "roster" partially visible; (4) "Summary Generator" — a document icon with bullet points, a clock showing 10:00, and a Slack channel icon. Arrows connecting the boxes are labeled: "DM events → parse → store → aggregate → post." A cron clock icon hovers above box 2 labeled "9:00 AM scheduler." The background is a subtle grid pattern suggesting an engineering whiteboard. Color-coded by component type: orange for scheduler, green for application logic, blue for data, purple for Slack. Labels in clean monospace font. 16:9 widescreen format. Style: modern tech illustration, Notion-like documentation aesthetic.

---

## Prompt 3 — User Journey Focus (Team Member POV)

**Best for:** onboarding tutorial, mobile app store screenshot mockup, user guide

**Prompt:**

A phone screen mockup sequence showing the Daily Standup Bot user experience from a team member's perspective. Three phone frames arranged side by side at a slight angle with drop shadows, set against a soft gradient background (white to pale lavender). Left frame: A Slack DM from "Standup Bot" at 9:00 AM showing the prompt card with three input fields — "Yesterday:", "Today:", "Blockers:" — each with a placeholder text hint in light gray. Center frame: The user has typed responses — "Yesterday: Finished the auth middleware. Today: Starting rate limiter. Blockers: None." A glowing "Send" button at the bottom. Right frame: The bot replies with a confirmation card: a green checkmark circle, "Response recorded! ✓" in bold, and "9/10 team members responded" in smaller type below. Above the three phones, a floating card shows the final summary as it appears in the team channel — a clean formatted list with one entry highlighted in amber for a blocker. Caption at bottom: "From prompt to team summary in under an hour." Warm, approachable illustration style. Slightly rounded corners on all UI elements. 9:16 portrait format (mobile-optimized).

---

## Style Notes

All three prompts share these constraints:
- No real human faces (illustrated characters only)
- No trademarked logos (use color/icon suggestions, not actual Slack logo)
- No text content that is too small to read at the target print/screen size
- Consistent color palette where possible: Slack purple, Node.js green, PostgreSQL blue

**Recommended generator:** Midjourney v6 or DALL·E 3 with the exact prompt text above. For Midjourney, append `--ar 11:17 --style raw --q 2` to Prompt 1, and `--ar 16:9` to Prompt 2.
