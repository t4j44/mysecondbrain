# Taj’s Second Brain // Retro-Futuristic Founder Terminal Design System

The visual identity of Taj’s Second Brain is engineered to deliver a **stunning, high-contrast, state-of-the-art "Retro-Futuristic Founder Terminal"**. It bridges cyberpunk high-tech hacker consoles with refined executive minimalism to keep the operator fully immersed in high-velocity execution.

---

## 1. Core Color Tokens & Contrast Motif

Our color palette avoids generic web presets, employing deep space purples contrasted against energetic neon cyan-greens and warm cream fonts.

| Token Usage | Hex Code | Tailwind / Custom Token | Visual Role & Component Assignment |
| :--- | :--- | :--- | :--- |
| **Deep Space Purple** | `#12081d` | `bg-background` / `dark:bg-[#12081d]` | Main application workspace background canvas and dashboard cards. |
| **Obsidian Void** | `#0a0510` | `bg-[#0a0510]` | Persistent Sidebar, command modaled popovers, and elevated modal headers. |
| **Warm Terminal Cream**| `#f7f4ea` | `text-[#f7f4ea]` / `text-cream` | High-readability primary body copy and bold executive headings. |
| **Electric Neon Green**| `#00ff9d` | `text-[#00ff9d]` / `border-[#00ff9d]` | Active interactive triggers, RLS status pulses, RAG AI badges, and focus borders. |
| **Muted Velvet Border**| `#251238` | `border-[#251238]` / `border-border`| Subtle structural grid dividers, card boundaries, and inactive tab borders. |

---

## 2. Typography Strategy

The console utilizes a strict dual-font hierarchy configured in `app/layout.tsx`:

1. **Primary Interface Font (`font-sans`)**: **Inter** via Google Fonts. Used for body paragraphs, CRM contact notes, descriptive subtitles, and long-form document reading.
2. **Terminal Console Font (`font-mono`)**: **JetBrains Mono** via Google Fonts. Used for all primary actions, status badges, telemetry KPIs, timestamp metadata, keyboard shortcuts (`Ctrl+K`), and system diagnostic notifications.

---

## 3. Component Architecture & Usage Guidance

### Primitives (`components/ui/`)
- **`Button`**: Offers standard fills plus a distinct `variant="terminal"` featuring JetBrains Mono font, uppercase letter-spacing, and subtle neon border glow upon hover.
- **`Input`**: High-contrast dark backgrounds (`#0e0716`) with electric green ring illumination (`focus:ring-[#00ff9d]`) upon operator focus.
- **`Card`**: Styled with dark velvet backgrounds and subtle box shadows (`shadow-[0_4px_20px_rgba(0,0,0,0.4)]`), ensuring content depth across complex data tables.

### Product Shared Components (`components/shared/`)
- **`AIInsightPanel`**: Special display frame for AI synthesized advice and RAG citations. Marked with neon corner gradients, confidence percentages, and source citation counts to reinforce zero-hallucination protocols.
- **`StatusBadge` & `PriorityBadge`**: Standardized tags matching PostgreSQL check constraints (`active`, `planning`, `paused`, `urgent`, `high`, `low`) directly to custom terminal icons and pulse animations.
- **`EmptyState` & `ErrorState`**: Replace plain browser fallbacks with dashed-border terminal illustrations, custom actions, and FastAPI request tracing ID copy slots.

---

## 4. Micro-Animations & Dynamic Feedback

An interface that feels responsive and alive encourages high user engagement. All transitions leverage Framer Motion or Tailwind UI utilities:
- **Subtle Glow Pulse (`animate-pulse-slow`)**: Used on active operator green status dots and urgent priority indicators.
- **Modal Viewport Zoom (`animate-in zoom-in-95 duration-150`)**: Ensures dialog modals and the Command Palette (`Ctrl+K`) open instantaneously without visual juddering.
- **Interactive Touch Feedback**: Buttons execute a subtle brightness elevation and transform scale transition when activated.

---

## 5. Accessibility & Responsive Standards

- **Minimum Touch Targets**: Every mobile interactive link in `MobileNavigation` and button action exceeds **44x44px** area dimensions, fully conforming to WCAG touch target criteria.
- **Keyboard Mastery**: Full keyboard navigation across all interactive elements. Pressing `Ctrl+K` (or `Cmd+K` on macOS) immediately traps focus inside the global Command Palette from any workspace screen.
- **Screen Reader Support**: All visual iconography embeds appropriate ARIA attributes (`aria-hidden="true"`, `role="alertdialog"`) accompanied by screen-reader text alternatives.
