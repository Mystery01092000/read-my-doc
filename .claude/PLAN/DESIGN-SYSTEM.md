# Design System & UI Guidelines
## Ask My Docs

**Version:** 1.0  
**Date:** 2026-04-04  
**Framework:** Tailwind CSS v3 · shadcn/ui conventions

---

## Table of Contents

1. [Design Principles](#1-design-principles)
2. [Color System](#2-color-system)
3. [Typography](#3-typography)
4. [Spacing & Layout Grid](#4-spacing--layout-grid)
5. [Component Library](#5-component-library)
6. [Page Layouts](#6-page-layouts)
7. [States & Feedback](#7-states--feedback)
8. [Iconography](#8-iconography)
9. [Motion & Animation](#9-motion--animation)
10. [Dark Mode](#10-dark-mode)
11. [Accessibility](#11-accessibility)
12. [Responsive Breakpoints](#12-responsive-breakpoints)
13. [Component Build Roadmap](#13-component-build-roadmap)

---

## 1. Design Principles

### 1.1 Clarity over cleverness
Every UI element must be immediately understandable. Labels beat icons. Explicit beats implicit.

### 1.2 Density without clutter
Information-dense layouts are preferred for productivity tools. Use tight spacing but always preserve breathing room between unrelated elements.

### 1.3 Progressive disclosure
Surface the most critical information first. Reveal secondary information on demand (e.g., citation details in a popover, not inline).

### 1.4 Feedback at every action
Users should always know: what just happened, what is happening now, and what they can do next. Never leave a loading state without a spinner or skeleton.

### 1.5 Accessible defaults
WCAG AA compliance is the baseline. Minimum contrast ratio 4.5:1 for body text, 3:1 for large text and UI components.

---

## 2. Color System

### 2.1 Brand Palette

Defined in `tailwind.config.ts`:

```
brand-50   #eff6ff   Hover backgrounds, selected row tints
brand-500  #3b82f6   Focus rings, active indicators
brand-600  #2563eb   Primary buttons, links
brand-700  #1d4ed8   Button hover states
```

### 2.2 Neutral Palette (Tailwind gray)

```
gray-50    #f9fafb   Page background (light)
gray-100   #f3f4f6   Hover background for list items
gray-200   #e5e7eb   Borders, dividers
gray-300   #d1d5db   Input borders
gray-400   #9ca3af   Placeholder text, disabled text
gray-500   #6b7280   Secondary text, captions
gray-700   #374151   Body text on light backgrounds
gray-800   #1f2937   Component backgrounds (dark mode)
gray-900   #111827   Panel backgrounds (dark mode)
gray-950   #030712   Page background (dark mode)
```

### 2.3 Semantic Colors

| Role | Light | Dark | Tailwind class prefix |
|------|-------|------|-----------------------|
| Success | `#16a34a` green-700 | `#4ade80` green-400 | `green-*` |
| Warning | `#d97706` yellow-600 | `#fcd34d` yellow-300 | `yellow-*` |
| Error | `#dc2626` red-600 | `#f87171` red-400 | `red-*` |
| Info | `#2563eb` blue-600 | `#60a5fa` blue-400 | `blue-*` |

### 2.4 Document Status Colors

| Status | Badge background | Badge text |
|--------|-----------------|------------|
| pending | `bg-yellow-100` | `text-yellow-800` |
| processing | `bg-blue-100` | `text-blue-800` |
| ready | `bg-green-100` | `text-green-800` |
| failed | `bg-red-100` | `text-red-800` |

Dark mode variants: replace `100` → `950`, `800` → `400`.

### 2.5 Color Usage Rules

- **Never** use raw hex values in JSX — always use Tailwind color tokens
- **Never** convey information by color alone — always pair with text or icon
- Brand-600 is the **only** color for primary interactive elements (buttons, links)
- Red is reserved for **destructive actions and errors only**

---

## 3. Typography

### 3.1 Font Stack

```css
font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
             "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
```

Tailwind's default system font stack — no custom font loading, fast TTFB.

### 3.2 Type Scale

| Role | Class | Size | Weight | Line Height |
|------|-------|------|--------|-------------|
| App name / hero | `text-2xl font-bold` | 24px | 700 | 32px |
| Page title | `text-xl font-semibold` | 20px | 600 | 28px |
| Section heading | `text-base font-semibold` | 16px | 600 | 24px |
| Body text | `text-sm` | 14px | 400 | 20px |
| Label | `text-sm font-medium` | 14px | 500 | 20px |
| Caption / meta | `text-xs` | 12px | 400 | 16px |
| Code / mono | `text-xs font-mono` | 12px | 400 | 16px |

### 3.3 Text Color

```
Primary content:   text-gray-900 dark:text-gray-50
Secondary content: text-gray-600 dark:text-gray-400
Muted / captions:  text-gray-400 dark:text-gray-500
Disabled:          text-gray-300 dark:text-gray-600
Links:             text-brand-600 hover:text-brand-700
Error:             text-red-600 dark:text-red-400
```

### 3.4 Chat Message Typography

Assistant messages use `prose prose-sm dark:prose-invert` from `@tailwindcss/typography` to render markdown correctly (headings, code blocks, lists, bold/italic).

---

## 4. Spacing & Layout Grid

### 4.1 Spacing Scale

Use Tailwind's default 4px base unit:

```
1 = 4px     2 = 8px     3 = 12px    4 = 16px
5 = 20px    6 = 24px    8 = 32px    10 = 40px
12 = 48px   16 = 64px
```

### 4.2 Layout Dimensions

| Element | Value |
|---------|-------|
| Sidebar width | `w-64` (256px) |
| Max content width (docs page) | `max-w-4xl` (896px) |
| Max content width (chat input bar) | `max-w-3xl` (768px) |
| Modal max width | `max-w-md` (448px) |
| Citation drawer max width | `max-w-lg` (512px) |

### 4.3 Padding Conventions

| Context | Padding |
|---------|---------|
| Page container | `p-6` |
| Card / panel | `px-5 py-4` |
| Button (default) | `px-4 py-2` |
| Button (compact) | `px-3 py-1.5` |
| Input | `px-3 py-2` |
| Modal | `p-6` |
| Sidebar item | `px-4 py-2.5` |

### 4.4 Vertical Rhythm

```
Space between page sections:  mb-6
Space between list items:      space-y-3
Space between form fields:     space-y-4
Space between inline elements: gap-2 or gap-3
```

---

## 5. Component Library

### 5.1 Button

```
Variants:    primary | ghost | destructive
Sizes:       default (px-4 py-2) | compact (px-3 py-1.5) | icon (p-2)
States:      default | hover | disabled | loading
```

**Primary button:**
```
bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-sm font-medium
disabled:opacity-50 disabled:cursor-not-allowed transition-colors
```

**Ghost button (text only):**
```
text-gray-600 hover:text-gray-900 dark:hover:text-gray-100 text-sm
```

**Destructive:**
```
text-red-500 hover:text-red-700 text-xs
```

---

### 5.2 Input

```
All inputs share a base class:
"w-full rounded-lg border border-gray-300 dark:border-gray-700
 bg-white dark:bg-gray-800 px-3 py-2 text-sm
 text-gray-900 dark:text-gray-100 placeholder-gray-400
 focus:outline-none focus:ring-2 focus:ring-brand-500"
```

**Textarea (chat input):**
```
Same base + "resize-none" + dynamic rows
```

---

### 5.3 Badge / Status Chip

```tsx
// Document status badge
<span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLORS[status]}`}>
  {status}
</span>

// Citation chip
<button className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium
  bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300
  hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors">
  [1]
</button>
```

---

### 5.4 Card / Panel

```
"rounded-xl border border-gray-200 dark:border-gray-800
 bg-white dark:bg-gray-900 px-5 py-4"
```

For interactive cards (hoverable list items):
```
"... hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer"
```

---

### 5.5 Modal / Overlay

**Backdrop:**
```
"fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-black/40"
```

**Modal panel:**
```
"w-full max-w-md rounded-xl bg-white dark:bg-gray-900
 border border-gray-200 dark:border-gray-700 shadow-xl p-6"
```

**Interaction:** clicking the backdrop closes the modal. The panel stops propagation.

---

### 5.6 Upload Dropzone

```
Normal state:
"rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-700
 hover:border-brand-400 p-10 text-center cursor-pointer transition-colors"

Active drag state:
"border-brand-500 bg-brand-50 dark:bg-brand-950"
```

---

### 5.7 Sidebar Navigation Item

```
Active:
"bg-brand-50 dark:bg-brand-900/30 text-brand-700 dark:text-brand-300 font-medium"

Inactive:
"text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"

Shared:
"block px-4 py-2.5 text-sm truncate transition-colors"
```

---

### 5.8 Message Bubble

```
User (right-aligned):
"max-w-[80%] rounded-2xl rounded-br-sm px-4 py-3 text-sm
 bg-brand-600 text-white"

Assistant (left-aligned):
"max-w-[80%] rounded-2xl rounded-bl-sm px-4 py-3 text-sm
 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700
 text-gray-900 dark:text-gray-100"
```

The asymmetric rounding (`rounded-br-sm` / `rounded-bl-sm`) creates the speech-bubble tail effect.

---

### 5.9 Streaming Cursor

```tsx
{isStreaming && (
  <span className="inline-block w-1.5 h-4 bg-gray-400 animate-pulse ml-1 align-middle" />
)}
```

---

## 6. Page Layouts

### 6.1 Auth Pages (Login / Register)

```
Full-screen centered column:

┌──────────────────────────────────────────────────────┐
│                   bg-gray-50 dark:bg-gray-950         │
│                                                        │
│              ┌─────────────────────────┐              │
│              │   App name (centered)   │              │
│              │   Subtitle              │              │
│              │                         │              │
│              │   ┌─────────────────┐   │              │
│              │   │    Form card    │   │              │
│              │   │  max-w-sm       │   │              │
│              │   └─────────────────┘   │              │
│              └─────────────────────────┘              │
└──────────────────────────────────────────────────────┘
```

### 6.2 App Layout (Documents / Chat)

```
Fixed-height viewport split:

┌──────────┬──────────────────────────────────────────┐
│          │                                            │
│ Sidebar  │              Main Content                  │
│  w-64    │              flex-1                        │
│          │                                            │
│ Session  │   /documents → DocumentsPage              │
│ list     │   /chat/:id  → ChatPage                   │
│          │                                            │
│          │                                            │
│ Sign out │                                            │
└──────────┴──────────────────────────────────────────┘
   h-screen  overflow-hidden (each pane scrolls independently)
```

### 6.3 Chat Page Layout

```
┌──────────────────────────────────────────────────────┐
│                                                        │
│   Messages area (flex-1, overflow-y-auto, py-6 px-4)  │
│                                                        │
│   ┌─────────────────────────────────────────────┐     │
│   │  [User message right-aligned]              │     │
│   └─────────────────────────────────────────────┘     │
│   ┌───────────────────────────────┐                   │
│   │  [Assistant message left]     │                   │
│   │  [1] [2] ← citation chips     │                   │
│   └───────────────────────────────┘                   │
│                                                        │
├──────────────────────────────────────────────────────┤
│   Input bar (border-t, py-3 px-4)                     │
│   ┌──────────────────────────────┐  ┌──────────┐      │
│   │  Textarea (flex-1)           │  │  Send    │      │
│   └──────────────────────────────┘  └──────────┘      │
└──────────────────────────────────────────────────────┘
```

### 6.4 Documents Page Layout

```
┌──────────────────────────────────────────────────────┐
│   Documents (max-w-4xl mx-auto p-6)                   │
│                                                        │
│   ┌──────────────────────────────────────────────┐    │
│   │  Dropzone (rounded-xl border-dashed)         │    │
│   └──────────────────────────────────────────────┘    │
│                                                        │
│   ┌──────────────────────────────────────────────┐    │
│   │  doc.txt  [ready]              [Delete]      │    │
│   ├──────────────────────────────────────────────┤    │
│   │  report.pdf  [processing]      [Delete]      │    │
│   ├──────────────────────────────────────────────┤    │
│   │  data.csv  [pending]           [Delete]      │    │
│   └──────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────┘
```

---

## 7. States & Feedback

### 7.1 Loading States

| Context | Pattern |
|---------|---------|
| Button submitting | Text changes: "Sign in" → "Signing in…" + `disabled` |
| Document uploading | "Uploading…" text in dropzone |
| Stream generating | Animated cursor (pulsing block) at end of message |
| Creating session | "Creating…" button text |

No full-page spinners. Always show feedback closest to the triggering element.

### 7.2 Error States

| Context | Pattern |
|---------|---------|
| Form errors (auth) | Red banner inside the form card above submit button |
| Upload errors | Red banner above document list |
| Chat errors | Inline text in gray centered below messages |
| Toast (future) | Bottom-right toast stack |

Error banners:
```
"rounded-md bg-red-50 dark:bg-red-950 px-4 py-3 text-sm text-red-600 dark:text-red-400"
```

### 7.3 Empty States

| Page | Empty message |
|------|--------------|
| Documents — no docs | "No documents yet. Upload one above." |
| Documents list — 0 sessions in sidebar | "No chats yet. Start a new one." |
| Chat — new session | "Ask a question about your documents." |
| New chat modal — no ready docs | "No ready documents. Upload and process some first." |

Empty state text: `text-center text-sm text-gray-400`.

### 7.4 Success States

No persistent success banners. Success is communicated by:
- Navigation to the resulting state (login → documents page)
- Updated list (upload → document appears with `pending` badge)
- Disappeared item (delete → row removed)

### 7.5 Document Status Lifecycle

```
Upload triggered
      │
      ▼
  [pending]   → yellow badge → "Document queued for processing"
      │
      ▼ (Celery worker picks up)
  [processing] → blue badge → spinning indicator (future)
      │
      ├──► [ready]   → green badge → "Ready to chat"
      │
      └──► [failed]  → red badge → error_message shown on hover (future)
```

---

## 8. Iconography

Using `lucide-react`. Import only what is used (tree-shaken by Vite).

### Icon Size Conventions

```
text / inline:   w-4 h-4  (16px)
button icon:     w-5 h-5  (20px)
feature icon:    w-6 h-6  (24px)
```

### Planned Icon Usage

| Context | Icon | Package |
|---------|------|---------|
| Upload | `Upload` or `CloudUpload` | lucide-react |
| Document | `FileText` | lucide-react |
| Chat / session | `MessageSquare` | lucide-react |
| Delete | `Trash2` | lucide-react |
| Close / dismiss | `X` | lucide-react |
| New chat | `Plus` | lucide-react |
| Dark mode toggle | `Sun` / `Moon` | lucide-react |
| Citation / source | `BookOpen` | lucide-react |
| Sign out | `LogOut` | lucide-react |
| Settings | `Settings` | lucide-react |

Icons are currently not used in v1 (text labels used instead). Add icons when implementing the polished component library.

---

## 9. Motion & Animation

### Philosophy
Minimal animation. Motion serves communication, not decoration.

### Animation Budget

| Element | Animation | Duration |
|---------|-----------|----------|
| Streaming cursor | `animate-pulse` | Tailwind default (2s) |
| Button hover | `transition-colors` | 150ms |
| Modal open (future) | fade in + scale up | 150ms |
| Toast (future) | slide in from bottom-right | 200ms |
| Sidebar item hover | `transition-colors` | 150ms |

### No Animation For
- Page transitions (instant navigation is appropriate for productivity tools)
- List items (no staggered entrances)
- Document status badge changes (polling is already async — just swap the class)

---

## 10. Dark Mode

### Implementation

- Strategy: Tailwind `darkMode: "class"` — `dark` class on `<html>`
- Persistence: `localStorage` key `theme` via `useDarkMode` hook
- System default: `window.matchMedia("(prefers-color-scheme: dark)")` on first visit

### Dark Mode Pairs

Every light color has a dark counterpart in the component markup:

```
bg-white              → dark:bg-gray-900      (panels/cards)
bg-gray-50            → dark:bg-gray-950      (page background)
bg-gray-100           → dark:bg-gray-800      (hover backgrounds)
border-gray-200       → dark:border-gray-800  (borders)
border-gray-300       → dark:border-gray-700  (input borders)
text-gray-900         → dark:text-gray-50     (primary text)
text-gray-600         → dark:text-gray-400    (secondary text)
text-gray-400         → dark:text-gray-500    (muted text)
```

### Adding Dark Mode Toggle (planned)

```tsx
// In SessionSidebar footer
import { useDarkMode } from "@/hooks/useDarkMode"
const { isDark, toggle } = useDarkMode()

<button onClick={toggle}>
  {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
</button>
```

---

## 11. Accessibility

### Standards

- WCAG 2.1 Level AA
- All interactive elements must be keyboard-navigable
- Screen reader announcements for async state changes (future: `aria-live` regions)

### Current Implementation

| Element | Accessibility |
|---------|--------------|
| Form inputs | `id` + `<label htmlFor>` for all inputs |
| Buttons | Descriptive text content (no icon-only buttons) |
| Modal | Closes on backdrop click and `Esc` key (future) |
| Focus ring | `focus:outline-none focus:ring-2 focus:ring-brand-500` on all interactive elements |

### Planned Improvements

- `aria-live="polite"` on document status changes
- `role="dialog"` + `aria-modal="true"` on modals
- `aria-busy="true"` on loading states
- Skip-to-content link
- Keyboard trap in open modals (`focus-trap-react`)

### Color Contrast Targets

| Pair | Ratio | Pass |
|------|-------|------|
| brand-600 on white | 4.57:1 | ✅ AA |
| gray-700 on white | 9.73:1 | ✅ AAA |
| gray-500 on white | 3.95:1 | ⚠️ AA large only |
| white on brand-600 | 4.57:1 | ✅ AA |

For body text, always use `text-gray-700` minimum (not `text-gray-500`) on light backgrounds.

---

## 12. Responsive Breakpoints

Tailwind's default breakpoints:

```
sm:   640px   Tablets
md:   768px   Small laptops
lg:   1024px  Laptops
xl:   1280px  Desktops
2xl:  1536px  Large screens
```

### Current Responsive Behavior

| Element | Mobile (<640px) | Tablet+ |
|---------|----------------|---------|
| Auth cards | Full-width with `px-4` | `max-w-sm` centered |
| Modal | `items-end` (sheet from bottom) | `items-center` (dialog) |
| Layout (sidebar) | Not yet adapted | Side-by-side |

### Mobile Adaptation (planned)

The sidebar collapses to an off-canvas drawer on mobile (`md:` breakpoint):

```
Mobile: Hamburger menu → overlay sidebar
Tablet+: Permanent sidebar
```

Document list and chat adapt via `px-4` padding and `max-w-full`.

---

## 13. Component Build Roadmap

Components to extract as the codebase grows:

### Phase A — Primitives (extract when used 3+ times)

| Component | Props | Notes |
|-----------|-------|-------|
| `Button` | `variant`, `size`, `isLoading`, `disabled` | Replaces inline class combos |
| `Input` | `label`, `error`, `type` | Wraps label + input + error message |
| `Badge` | `label`, `variant` | Status chips, document type chips |
| `Spinner` | `size` | Loading indicator for buttons / pages |

### Phase B — Layouts

| Component | Props | Notes |
|-----------|-------|-------|
| `Modal` | `open`, `onClose`, `title` | Focus trap, ESC handler, backdrop |
| `Toast` | `message`, `type`, `duration` | Global toast queue via zustand |
| `EmptyState` | `message`, `action?` | Centered empty state with optional CTA |

### Phase C — Domain Components

| Component | Domain | Notes |
|-----------|--------|-------|
| `DocumentCard` | Documents | Replace inline list item |
| `MessageList` | Chat | Extract scrollable messages area |
| `SessionItem` | History | Replace sidebar link |
| `CitationDrawer` | Chat | Full source chunk drawer (vs modal) |

### Extraction Rule

Extract a component when:
1. The same HTML + class combo appears in **3 or more** places, OR
2. The component has meaningful internal state (e.g., `CitationChip` toggle), OR
3. The component requires accessibility attributes that are easy to forget

Do **not** extract prematurely — a two-use case is often better left inline.
