# Next Generation Prompt: Bento Evolution

## Current Design System: Obsidian Intelligence Framework
- **Core Aesthetic:** Deep Slate (#0b1326), Corporate Blue (#007BFF), Glassmorphism (32px blur), Plus Jakarta Sans headers.

## Bento Grid Layout Rules (from BENTO_GRID.md)
- **Responsive Grid:** 1 column on mobile, 3 columns on tablet/desktop (grid-cols-3).
- **Items Style:** Rounded-xl corners, border-white/10 dark, bg-black dark, subtle hover lift (-translate-y-0.5).
- **Logic:** Each Bento item must have:
    - `colSpan` (default 1, col-span-2 for main features).
    - `icon`: Using `lucide-react` icons (TrendingUp, CheckCircle, Globe, etc.).
    - `status`: Minimal status chip (Live, Updated, Beta).
    - `meta`: Small technical metadata (v2.4.1, 12GB used).
    - `tags`: Small hashtags (#Statistics, #AI).

## Target Screen: Documents Management (Bento)
- **Tile 1 (col-span-2):** "Knowledge Base Stats" - Real-time metrics on your document corpus.
- **Tile 2 (col-span-1):** "Active Sessions" - Link to the last Chat session.
- **Tile 3 (col-span-3):** "Document Hive" - Your high-density document list, replacing traditional tables with a Bento-style card list.
- **Tile 4 (col-span-1):** "Rapid Context Upload" - Drag & drop zone.
- **Tile 5 (col-span-2):** "System Health" - API connectivity and storage status.

## Branding: ReadMyDoc
Ensure the name is consistent in the top-left or centered as a focal Bento item.
