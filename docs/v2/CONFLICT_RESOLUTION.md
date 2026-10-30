# V2 reconciliation decisions

Base `50890449cef9a68a73808383d12d257d0e1cb5aa` retains meeting, MCP, Google, relationship and mobile performance work. Changes were ported into a new isolated branch; source branches and PRs remain intact.

| Input | Resolution |
|---|---|
| [PR13](https://github.com/t4j44/mysecondbrain/pull/13), `f98ac657c3e617b660621f2236f40ee9d6fe3c08` | Port its eight UI files. Retain compact shell, cards and spacing. Home says Today and describes only the current view. Capture says Review capture because this action proposes, not saves. No brand redesign. |
| [PR14](https://github.com/t4j44/mysecondbrain/pull/14), `16c45f49b112a90a1dbf1cb741f05385358750c7` | Port its meeting overview/search/filter. Keep CapturePanel mounted while collapsed; disable collapse during recording/upload; preserve title, consent and recovery state. |
| PR14 zero counters during loading/failure | Show overview only after successful nonempty load. Empty accounts get an actionable capture prompt. |
| PR14 failed/draft counted as processing | Processing includes actual recording/upload/transcription/extraction only. Failed records retain explicit retry status. |
| Legacy five destinations vs V2 | PR0 preserves existing navigation; next workstream adopts Home / People / Capture / Meetings / More with routes preserved. |
| Legacy Pillow requirement | Align requirements.txt to existing locked/pyproject 13.x family; retain hash locking and tests. |

Capture regression exercises real React recording controls with labelled synthetic recorder/provider adapters: collapse/reopen retains title/consent; active capture cannot be hidden/disposed; ending performs the existing upload/finalization. It does not prove physical microphone or hosted provider delivery.
