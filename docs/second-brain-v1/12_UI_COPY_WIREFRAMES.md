# UI Copy, Low-Fidelity Wireframes and Accessibility Microcopy
Design artifacts here are **text wireframes**, not current product screenshots. All copy is proposed English-first, subject to user testing and consent/legal review.

## 1. Desktop Shell
```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ Second Brain             Search anything… [⌘K]        [+ Capture]   Help   Profile  │
├─────────────────┬──────────────────────────────────────────────────────────────────┤
│ Home            │ Good morning                                                     │
│ People          │ Here's what needs attention — based on your saved context        │
│ Meetings        │                                                                  │
│ Work            │ NEXT UP             OUTSTANDING PROMISES                         │
│ Ask             │ [Meeting with A]   [Send update to B — due tomorrow]              │
│                 │                                                                  │
│ ───────────     │ RECENT CONTEXT                                                 │
│ Files & sources │ Meeting with A · 2 cited decisions · Review                      │
│ Integrations    │ Person B · Last interaction 3d ago · Open                       │
│ Settings        │                                                                  │
│                 │ [Capture a note]  [Record meeting]  [Find a person]               │
└─────────────────┴──────────────────────────────────────────────────────────────────┘
```
No actual user data may be invented for a live empty account; show real or explicitly fictional demo labels only.

## 2. Mobile Shell
```
┌──────────────────────────┐
│ Second Brain      [+]    │
│ Search anything...       │
│                          │
│ Today                    │
│ Your next useful step    │
│ [Review 1 pending item]  │
│                          │
│ Upcoming                 │
│ [Meeting card]           │
│                          │
│ Recent conversations     │
│ [Person + source card]   │
│                          │
├──────────────────────────┤
│ Home People Meet Work Ask│
└──────────────────────────┘
```
Tap sizes >= practical ~44px; screen-reader says "Meetings" even if visual label shortens.

## 3. People detail
```
[← People]   Sarah Chen                 [Edit] [More]
Relationship summary (user-editable)
Last spoke 9 Nov · 3 linked conversations

What matters now
[Promise: Send draft proposal] [Due tomorrow] [View source]

Timeline
9 Nov  Meeting: discussed launch · [Transcript 08:41]
4 Nov  Note: budget decision · [Open original]

[+ Add interaction] [Prepare next meeting]
```
All example names/dates are illustrative, not actual test evidence.

## 4. Meeting detail
```
[← Meetings]  Partnership discussion    [Record another]  [More]
Status: Ready for review · 2 speakers
[Summary]  [Decisions & actions]  [Transcript]  [Audio]

Summary (AI draft — verify sources)
"We agreed to review pricing." [Source 07:25]

Decisions & actions
[ ] Send draft proposal by Friday [Source 08:41]
    [Confirm] [Edit] [Reject]

Original recording — available until [date]
[▶ Play] [↓ Download original]  .m4a · 12 MB

[Search transcript...]  Speaker 1 · 08:41 ...
```
Avoid the label "AI verified" unless a real independent check occurred; otherwise say "AI draft". If audio expired: "The original recording is no longer stored. Your transcript remains available under your retention settings."

## 5. Meetings > Schedule
```
Meetings / Schedule
[My availability] [Booking links] [Calendar connections]

Your booking links
[30-minute introduction] Active   [Copy link] [Edit]
[+ Create booking link]

Connected calendar: Not connected
[Connect calendar] or [Download an .ics invite manually]
```
Public guest page must contain only public host name/booking description, not private People or conversation context.

## 6. Ask
```
Ask Second Brain
[What did I promise Sarah in the last two meetings?    ] [Ask]

Based on 2 saved meetings and 1 confirmed note:
• You confirmed a draft proposal due Friday. [9 Nov transcript, 08:41]
• A possible meeting follow-up was mentioned but not confirmed. [4 Nov, 11:02]

[Open sources] [Suggest a reminder] [Correct this]
```
If unsupported: "I couldn't find a reliable source for that. Try adding a note or linking a meeting." Not "I have everything in your memory".

## 7. Onboarding
**Headline:** "Remember what matters from your conversations."  
**Subtext:** "Save context. Track promises. Find the source when you need it."  
**Choices:** "Add a person" / "Capture a note" / "Record or upload a meeting".  
**Privacy prompt:** "Your information is private to your account. You decide what gets saved, linked or shared." (Validate this statement end-to-end.)  
**AI processing:** "Some AI features send information to an external provider. Review what can be processed before continuing." Include provider-specific facts; no blind consent.

## 8. Universal state language
| State | User-facing language | Action |
|---|---|---|
| Saving | "Saving your note…" | Keep draft, show progress |
| Saved | "Saved to your Second Brain" | Open record |
| Processing | "Reading your recording… you can leave this page" | Show valid actual job status |
| Failed (retryable) | "We couldn't finish processing. Your recording is safe here." | Retry upload |
| Needs review | "Check these suggestions before saving them" | Confirm/edit/reject |
| Missing evidence | "I couldn't verify that from your saved sources" | Open sources/Add context |
| Expired recording | "This recording has expired. The transcript is still available." | View transcript |
| No calendar permission | "Calendar isn't connected. You can still create a manual invite." | Connect/ICS |
| Waking service | "Connecting to your workspace…" | Controlled retry |
| Recording permission | "Only record conversations when everyone required has agreed." | Acknowledge consent |
| Data export | "Your export is being prepared. We'll show when it's ready." | View status |

## 9. Anti-pattern rejection list
Reject designs with 15 navigation tabs, big blank charts, nonsemantic AI jargon, a modal for each action, hidden consent, dark hacker/terminal aesthetics as the default, fake loading percentages, inaccessible icon-only buttons, permanently exposed raw audio URLs, invented citations or private content in demo screenshots.
