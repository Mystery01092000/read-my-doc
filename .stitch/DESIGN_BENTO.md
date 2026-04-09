# Design System: Bento Tech (ReadMyDoc)

## 1. Overview & Creative North Star
**Creative North Star: "The Information Hive"**
This design system is built for the post-SaaS era. It rejects the "sidebar + content" traditional layout in favor of an organized, high-density Bento Grid. It communicates "Technical Maturity" through a pure Black and White foundation, while using vibrant functional accents to signal state and priority.

---

## 2. Colors & Surface Philosophy (Source: BENTO_GRID.md)
The system leads with a high-contrast, professional palette.

- **Background:** `#000000` (Pure Black)
- **Surface:** `#000000`
- **Surface Container:** `#0a0a0a` (Subtle elevation)
- **Secondary (Accents):**
    - `Primary`: Blue-500 (`#3b82f6`) - Growth & Navigation
    - `Success`: Emerald-500 (`#10b981`) - Completion & Readiness
    - `Media`: Purple-500 (`#a855f7`) - Processing & Assets
    - `Info`: Sky-500 (`#0ea5e9`) - Infrastructure & Stats

### The "Bento Border" Rule
- **Border:** `1px solid rgba(255, 255, 255, 0.1)` (White @ 10%) for dark mode.
- **Glass:** No heavy blurs are required for the base grid, but a subtle `backdrop-blur-sm` can be used on floating chips.
- **Hover:** `-translate-y-0.5` with a scaling shadow `0 2px 12px rgba(255, 255, 255, 0.03)`.

---

## 3. Typography
Technical, clean, and weighted for information architecture.
- **Headers:** Plus Jakarta Sans (Weight: 600)
- **Body:** Inter (Weight: 425) - High legibility.
- **Metadata:** Inter (Weight: 400) - 13px/14px.

---

## 4. Components (BENTO_GRID.md Logic)

### Bento Tiles
- **Construction:** `rounded-xl` (12px), `p-4`, `overflow-hidden`.
- **States:** 
    - `Default`: Border-white/10, bg-black.
    - `Hover`: Border-white/20, shadow-white/03.
    - `Active`: Scale(1.02) or translate-y-0.5.

### Status Chips
- `bg-white/10`, `text-gray-300`, `rounded-lg`, `px-2`, `py-1`, `text-xs`.

### Lucide Icons
- 16px (w-4 h-4) icons in functional colors (Blue, Emerald, Purple, Sky).

---

## 5. Do’s and Don’ts

### Do
- **Do** use `col-span-2` or `col-span-3` for primary feature focus.
- **Do** align icons and headers consistently in the top-left of each tile.
- **Do** add "Explore ->" or "CTA" text in the bottom-right of interactive tiles.

### Don't
- **Don't** use 100% opaque borders. Keep them at 10% opacity for a "Ghost" feel.
- **Don't** use Deep Slate or Navy. This system is pure Black (#000) for "OLED" tech appeal.
- **Don't** mix non-Bento layouts on the same page.
---
