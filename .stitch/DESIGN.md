# Design System: The Obsidian Intelligence Framework

## 1. Overview & Creative North Star
**Creative North Star: "The Ethereal Executive"**
This design system moves away from the "SaaS-standard" boxy layout toward a high-end editorial experience. It envisions the interface not as a collection of widgets, but as a sophisticated digital workspace where AI intelligence is represented through light, depth, and atmospheric clarity. 

By leveraging **intentional asymmetry** and **tonal layering**, we break the rigid "template" look. We favor breathing room and overlapping glass surfaces over crowded grids, ensuring every interaction feels curated, premium, and calm.

---

## 2. Colors & Surface Philosophy
The palette is rooted in a deep, nocturnal Slate, punctuated by a hyper-precise Corporate Blue.

### Color Tokens (Material Convention)
- **Surface (Background):** `#0b1326` (Deep Slate)
- **Primary:** `#adc7ff` (Soft Blue Highlight)
- **Primary Container:** `#4a8eff` (Vibrant Action Blue)
- **On-Primary:** `#002e68` (Deep contrast text)
- **Surface Container Lowest:** `#060e20` (Inset depth)
- **Surface Container Highest:** `#2d3449` (Elevated glass)
- **Outline Variant:** `#414754` (Subtle boundary)

### The "No-Line" Rule
To achieve a signature high-end look, **prohibit 1px solid borders for sectioning.** Boundaries must be defined solely through background color shifts or tonal transitions. Use `surface_container_low` against a `surface` background to define regions. The eye should perceive change through depth, not strokes.

### The "Glass & Gradient" Rule
Floating elements (modals, dropdowns, floating nav) must utilize **Glassmorphism**:
- **Fill:** `surface_container_highest` at 60% opacity.
- **Effect:** 20px - 40px Backdrop Blur.
- **Edge:** A "Ghost Border" using `outline_variant` at 15% opacity to catch light.

### Signature Textures
Main CTAs and Hero sections should utilize a **Subtle Mesh Gradient**:
- Start: `primary_container` (#4a8eff)
- End: `secondary_container` (#0257b4)
- Angle: 135-degree radial flow to provide a sense of "visual soul."

---

## 3. Typography
The typographic system creates an editorial rhythm by pairing the geometric confidence of Plus Jakarta Sans with the utilitarian clarity of Inter.

| Role | Token | Font | Size | Weight |
| :--- | :--- | :--- | :--- | :--- |
| **Display** | `display-lg` | Plus Jakarta Sans | 3.5rem | 700 |
| **Headline** | `headline-md` | Plus Jakarta Sans | 1.75rem | 600 |
| **Title** | `title-lg` | Inter | 1.375rem | 500 |
| **Body** | `body-md` | Inter | 0.875rem | 400 |
| **Label** | `label-sm` | Inter | 0.6875rem | 600 |

---

## 4. Elevation & Depth
In this system, depth is a functional tool, not a decoration. We use **Tonal Layering** instead of structural lines.

- **The Layering Principle:** Place a `surface_container_lowest` card on a `surface_container_low` section to create a soft "recessed" effect.
- **Ambient Shadows:** For floating glass elements, use an extra-diffused shadow: `0px 24px 48px rgba(0, 0, 0, 0.4)`. The shadow should feel like a soft glow of darkness rather than a hard edge.
- **Ghost Border Fallback:** If a border is required for accessibility, it must be the `outline_variant` token at **max 20% opacity**. Never use 100% opaque lines.

---

## 5. Components

### Buttons (The Core Action)
- **Primary:** Gradient fill (`primary_container` to `#0056b3`). Use a soft `primary_fixed_dim` outer glow on hover (0px 0px 15px).
- **Secondary:** Glassmorphic background with a `primary` ghost border (15% opacity).
- **Radius:** `0.5rem (lg)` for a modern, professional feel.

### Glassmorphic Cards
- **Construction:** `surface_container_highest` @ 40% opacity + 32px Backdrop Blur.
- **Separation:** No dividers. Use 24px - 32px vertical padding to separate content blocks.
- **Interaction:** On hover, increase the opacity of the ghost border from 15% to 40%.

### Input Fields (Intelligence Inputs)
- **Style:** Underline-only or subtle `surface_container_lowest` fill.
- **Floating Labels:** Move from `body-md` to `label-sm` on focus, transitioning to the `primary` color.
- **Focus:** A 2px `primary_container` ring with a soft outer bloom.

---

## 6. Design System Notes for Stitch Generation
[Copy this block into every Stitch prompt]

**DESIGN SYSTEM (REQUIRED):**
- **Palette:** Slate-900 surface (#0b1326), Corporate Blue primary (#007BFF).
- **Typography:** Plus Jakarta Sans (Headlines), Inter (Body).
- **Theme:** Obsidian Intelligence Framework — "The Ethereal Executive".
- **Rule:** No 1px dividers. Use tonal layering and glassmorphism (surface_container_highest at 60% opacity with 32px blur).
- **Style:** 135-degree mesh gradients for CTAs. 0.5rem roundness.

---
