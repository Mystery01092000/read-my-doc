# Frontend Development Guide
## Ask My Docs

**Version:** 1.0  
**Date:** 2026-04-04  
**Stack:** React 18 · Vite · TypeScript · Tailwind CSS · Zustand · React Router v6

---

## Table of Contents

1. [Project Structure](#1-project-structure)
2. [Tech Stack & Dependencies](#2-tech-stack--dependencies)
3. [Routing Architecture](#3-routing-architecture)
4. [State Management](#4-state-management)
5. [API Layer](#5-api-layer)
6. [Feature Modules](#6-feature-modules)
7. [Component Conventions](#7-component-conventions)
8. [Typing Conventions](#8-typing-conventions)
9. [Styling System](#9-styling-system)
10. [SSE Streaming Pattern](#10-sse-streaming-pattern)
11. [Error Handling](#11-error-handling)
12. [Environment & Config](#12-environment--config)
13. [Local Development](#13-local-development)
14. [Build & Deploy](#14-build--deploy)
15. [Testing Strategy](#15-testing-strategy)
16. [Planned Enhancements](#16-planned-enhancements)

---

## 1. Project Structure

```
frontend/
├── public/
├── index.html
├── vite.config.ts          # Vite + proxy to backend API
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.js
├── nginx.conf              # Production SPA fallback + API proxy
├── Dockerfile              # Multi-stage: node builder → nginx runner
└── src/
    ├── main.tsx            # React root mount
    ├── App.tsx             # Route tree (BrowserRouter + Routes)
    ├── index.css           # Tailwind base + CSS custom properties
    │
    ├── types/
    │   └── index.ts        # All shared TypeScript interfaces
    │
    ├── api/                # Typed HTTP clients per domain
    │   ├── client.ts       # axios factory with auth interceptor
    │   ├── auth.ts         # authApi.register / login / refresh / logout
    │   ├── documents.ts    # documentsApi.list / upload / get / delete
    │   └── chat.ts         # chatApi.listSessions / createSession / sendMessage
    │
    ├── store/
    │   └── useAuthStore.ts # Zustand auth store (persisted to localStorage)
    │
    ├── hooks/
    │   ├── useAuth.ts      # login / register / logout with navigation
    │   └── useDarkMode.ts  # dark mode toggle + localStorage persistence
    │
    ├── components/         # Shared, domain-agnostic UI components
    │   └── AppShell.tsx    # Layout: sidebar + <Outlet /> for main content
    │
    └── features/           # Domain feature modules (co-located)
        ├── auth/
        │   ├── LoginPage.tsx
        │   ├── RegisterPage.tsx
        │   └── RequireAuth.tsx     # Protected route wrapper
        ├── documents/
        │   └── DocumentsPage.tsx   # Upload dropzone + document list
        ├── chat/
        │   ├── ChatPage.tsx        # Main chat view with SSE streaming
        │   ├── MessageBubble.tsx   # Renders user/assistant messages
        │   └── CitationChip.tsx    # Clickable citation with source drawer
        └── history/
            └── SessionSidebar.tsx  # Left sidebar: session list + new chat modal
```

### Conventions

- **Co-locate by feature** — all files for a feature live in `features/<domain>/`
- **Shared components** — only in `components/` if used by 2+ features
- **No barrel re-exports** — import directly from the file that defines the thing
- **One component per file** — named export, filename matches component name

---

## 2. Tech Stack & Dependencies

### Core

| Package | Version | Purpose |
|---------|---------|---------|
| `react` | 18.3 | UI rendering |
| `react-dom` | 18.3 | DOM renderer |
| `react-router-dom` | 6.28 | Client-side routing |
| `axios` | 1.7 | HTTP client |
| `zustand` | 5.0 | Lightweight state management |
| `react-dropzone` | 14.3 | File upload drag-and-drop |
| `react-markdown` | 9.0 | Markdown rendering in chat messages |

### UI

| Package | Version | Purpose |
|---------|---------|---------|
| `tailwindcss` | 3.4 | Utility-first CSS |
| `lucide-react` | 0.468 | Icon set |
| `clsx` | 2.1 | Conditional class merging |
| `tailwind-merge` | 2.6 | Merge conflicting Tailwind classes |

### Dev Tools

| Package | Version | Purpose |
|---------|---------|---------|
| `vite` | 6.0 | Build tool + dev server |
| `typescript` | 5.7 | Static typing |
| `@vitejs/plugin-react` | 4.3 | React Fast Refresh |
| `eslint` | 9.17 | Linting |
| `@typescript-eslint/*` | 8.18 | TypeScript ESLint rules |

---

## 3. Routing Architecture

All routes are defined in `src/App.tsx`.

```
/login               → LoginPage        (public)
/register            → RegisterPage     (public)

/ (RequireAuth)
  └── (AppShell)
        ├── /documents         → DocumentsPage
        └── /chat/:sessionId   → ChatPage

/  (root)            → Redirect to /documents
```

### RequireAuth

`features/auth/RequireAuth.tsx` wraps protected routes:

```tsx
// Reads isAuthenticated() from useAuthStore
// → redirect to /login if not authenticated
// → renders <Outlet /> if authenticated
```

### AppShell

`components/AppShell.tsx` is the layout wrapper for authenticated pages:
- Renders `<SessionSidebar />` on the left
- Renders `<Outlet />` (the active page) on the right
- Fixed height `h-screen` with `overflow-hidden` — each section scrolls independently

### Navigation Rules

| From | Trigger | To |
|------|---------|----|
| Login success | `useAuth.login()` | `/documents` |
| Register success | `useAuth.register()` | `/documents` |
| New chat created | `SessionSidebar` | `/chat/:newId` |
| Logout | `useAuth.logout()` | `/login` |
| Unauthenticated access | `RequireAuth` | `/login` |

---

## 4. State Management

### Zustand Auth Store (`store/useAuthStore.ts`)

The only global store. Persisted to `localStorage` under key `amd-auth`.

```ts
interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  setTokens(access: string, refresh: string): void
  clearTokens(): void
  isAuthenticated(): boolean
}
```

**Rules:**
- Access `useAuthStore.getState()` in non-component contexts (API clients)
- Access `useAuthStore(selector)` inside components
- Never store user profile data in the store — fetch from `/auth/me` when needed

### Local State

All other state is local (`useState`) or derived from API calls. No additional global stores are needed for v1.

### Server State

No React Query / SWR in v1. API calls are managed manually with `useEffect` + `useState`. If the app grows, migrate to TanStack Query.

---

## 5. API Layer

### Client Factory (`api/client.ts`)

```ts
// Creates an axios instance with the auth interceptor
createApiClient(getToken: () => string | null): AxiosInstance

// Unauthenticated client for /auth/* endpoints
publicClient: AxiosInstance
```

**Pattern:** Each domain API file calls `createApiClient(() => useAuthStore.getState().accessToken)` inline — this lazily reads the current token each call, so it always uses the latest value after a refresh.

### Domain API Modules

```
api/auth.ts       authApi.register / login / refresh / logout
api/documents.ts  documentsApi.list / upload / get / delete
api/chat.ts       chatApi.listSessions / createSession / getSession / deleteSession / sendMessage
```

### SSE Streaming

`chatApi.sendMessage` does **not** use axios. SSE responses require the Fetch API with `ReadableStream`. See [Section 10](#10-sse-streaming-pattern) for the full pattern.

### API Base URL

Configured via `VITE_API_URL` env var (defaults to `/api`). The Vite dev server proxies `/api` → `http://localhost:8000`. In production, nginx handles the proxy.

### Error Handling Contract

All API functions throw on non-2xx responses. Callers catch errors and set local error state:

```ts
try {
  await documentsApi.delete(id)
} catch {
  setError("Failed to delete document")
}
```

---

## 6. Feature Modules

### Auth (`features/auth/`)

| File | Responsibility |
|------|---------------|
| `LoginPage.tsx` | Email + password form → `useAuth.login()` |
| `RegisterPage.tsx` | Register form with confirm password → `useAuth.register()` |
| `RequireAuth.tsx` | Route guard — redirects to `/login` if not authenticated |

**Form pattern:** Controlled inputs (`useState`), `onSubmit` calls the hook method, hook manages `isLoading` and `error`.

### Documents (`features/documents/`)

| File | Responsibility |
|------|---------------|
| `DocumentsPage.tsx` | Upload dropzone + paginated document list with status badges |

**Key behaviors:**
- `react-dropzone` for multi-file drag-and-drop
- Accepted MIME types mapped to extensions (`pdf`, `txt`, `md`, `csv`, `xlsx`, `pptx`)
- Polls every 5 seconds to update `pending` / `processing` statuses
- Polling clears on unmount via `clearInterval` in `useEffect` cleanup
- Status badge colors: `pending` → yellow, `processing` → blue, `ready` → green, `failed` → red

### Chat (`features/chat/`)

| File | Responsibility |
|------|---------------|
| `ChatPage.tsx` | Main chat view — message list + streaming input bar |
| `MessageBubble.tsx` | Renders user (right-aligned) or assistant (left-aligned) messages |
| `CitationChip.tsx` | Inline `[1]` badge that opens a source drawer on click |

**Key behaviors:**
- SSE stream: tokens appended to `streamingContent` state in real time
- Citations arrive as a final `citations` event; merged into the persisted message
- Session is reloaded after stream ends to get server-persisted messages
- `Enter` sends, `Shift+Enter` adds newline

### History (`features/history/`)

| File | Responsibility |
|------|---------------|
| `SessionSidebar.tsx` | Left sidebar with session list, logout, new chat modal |

**Key behaviors:**
- Session list reloads on `sessionId` param change (detects navigation)
- "New Chat" button opens a modal listing all `ready` documents
- Multi-select checkboxes — at least one must be selected to create session
- Session is auto-titled after first message (done server-side)

---

## 7. Component Conventions

### Naming

```
PascalCase      → components, pages (LoginPage, CitationChip)
camelCase       → hooks, stores, utilities (useAuth, useAuthStore)
kebab-case      → files that are not components (not currently used)
```

### Export Style

All components use **named exports**:

```tsx
// ✅ Correct
export function LoginPage() { ... }

// ❌ Avoid default exports for feature components
export default function LoginPage() { ... }
```

Exception: `src/App.tsx` uses a default export (required by Vite entry point convention).

### Props

- Inline interfaces for simple props
- Separate `interface Props { ... }` for components with 3+ props
- Never use `React.FC` — just type the function directly

```tsx
// ✅ 
interface Props {
  citation: Citation
  index: number
}
export function CitationChip({ citation, index }: Props) { ... }

// ✅ Simple — inline is fine
export function Badge({ label, color }: { label: string; color: string }) { ... }
```

### Event Handlers

Name as `handle<Event>` for DOM events, `on<Action>` for prop callbacks:

```tsx
// Internal handler
const handleSubmit = (e: FormEvent) => { ... }

// Prop callback
interface Props {
  onDelete: (id: string) => void
}
```

### Immutability in State Updates

Always return new objects/arrays — never mutate existing state:

```tsx
// ✅
setMessages((prev) => [...prev, newMessage])

// ❌
messages.push(newMessage)
setMessages(messages)
```

---

## 8. Typing Conventions

All shared types live in `src/types/index.ts`. Domain-specific types not shared across features may be defined locally.

### Key Types

```ts
// Auth
interface TokenPair { access_token: string; refresh_token: string; token_type: string }

// Documents
type DocumentStatus = "pending" | "processing" | "ready" | "failed"
type FileType = "pdf" | "txt" | "md" | "csv" | "xlsx" | "pptx"
interface Document { id: string; filename: string; fileType: FileType; ... }

// Chat
interface Citation { chunkId: string; documentId: string; filename: string; page: number | null; snippet: string }
interface Message { id: string; role: "user" | "assistant"; content: string; citations: Citation[]; createdAt: string }
interface ChatSession { id: string; title: string; documentIds: string[]; createdAt: string; updatedAt: string }

// Pagination
interface PaginatedResponse<T> { items: T[]; total: number; page: number; limit: number; pages: number }
```

### API Response Casing

The backend returns **snake_case** JSON. The frontend currently uses the raw API shape for auth (`access_token`, `refresh_token`) and camelCase for domain objects. When the backend adds a serialization layer, update the API response types in `types/index.ts`.

### No `any`

`tsconfig.json` has `"strict": true`. Never use `any`. Use `unknown` and narrow with type guards when receiving untyped data (e.g., SSE payloads).

---

## 9. Styling System

### Tailwind CSS

All styling is utility-first with Tailwind v3. No CSS modules, no styled-components.

### Color Palette

Defined in `tailwind.config.ts`:

```ts
brand: {
  50:  "#eff6ff",   // light hover backgrounds
  500: "#3b82f6",   // focus rings
  600: "#2563eb",   // primary buttons
  700: "#1d4ed8",   // button hover
}
```

All interactive elements use `brand-*` colors. Status colors use Tailwind's semantic palette (`green`, `yellow`, `blue`, `red`).

### Dark Mode

Implemented via the `class` strategy — `dark` class toggled on `<html>`. The `useDarkMode` hook manages persistence in `localStorage`.

Pattern for dark-mode-aware components:

```tsx
className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
```

### Spacing & Layout

| Context | Pattern |
|---------|---------|
| Page padding | `p-6` or `px-4 py-6` |
| Card/panel | `rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900` |
| Sections within panel | `space-y-4` |
| Inline gap | `gap-2` or `gap-3` |
| Max content width | `max-w-4xl mx-auto` (documents), `max-w-3xl mx-auto` (chat input) |

### Typography Scale

| Role | Class |
|------|-------|
| Page title | `text-2xl font-bold` |
| Section heading | `text-base font-semibold` |
| Body / labels | `text-sm` |
| Captions / meta | `text-xs` |
| Code / mono | `font-mono` |

### Reusable Class Combos (not extracted into components yet)

```
// Primary button
"rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"

// Text input
"w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"

// Card panel
"rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 px-5 py-4"
```

When a combo is used 3+ times, extract it into a `components/` primitive (e.g., `Button`, `Input`, `Card`).

---

## 10. SSE Streaming Pattern

The chat endpoint returns a Server-Sent Events stream as a POST response. Since `EventSource` only supports GET, we use the Fetch API with `ReadableStream`.

### Event Format

Each line from the server:

```
data: {"type": "token", "content": " word"}
data: {"type": "citations", "citations": [...]}
data: [DONE]
```

### Implementation Pattern (`api/chat.ts`)

```ts
fetch(`${BASE_URL}/chat/sessions/${sessionId}/messages`, {
  method: "POST",
  headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
  body: JSON.stringify({ content }),
})
.then(async (res) => {
  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split("\n")
    buffer = lines.pop() ?? ""   // keep incomplete last line

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue
      const data = line.slice(6).trim()
      if (data === "[DONE]") { onDone(); return }
      const parsed = JSON.parse(data)
      if (parsed.type === "token")     onToken(parsed.content)
      if (parsed.type === "citations") onCitations(parsed.citations)
    }
  }
})
```

### Component Pattern (`ChatPage.tsx`)

```tsx
const [streamingContent, setStreamingContent] = useState("")
// Tokens appended to streamingContent → displayed as a live preview
// On [DONE] → refresh session from server to get persisted message with citations
```

---

## 11. Error Handling

### API Errors

Every API call is wrapped in try/catch. Errors set local `error` state displayed as inline error banners.

```tsx
const [error, setError] = useState<string | null>(null)

try {
  await documentsApi.delete(id)
} catch {
  setError("Failed to delete document")
}
```

Never expose raw `axios` error messages to the user — use friendly strings.

### Auth Errors

- 401 from login/register → display "Invalid email or password" / "Email already registered"
- Token expiry is handled by clearing the store + redirecting to `/login` (to be implemented: axios response interceptor for auto-refresh)

### Form Validation

Client-side validation before API call:
- Password length check (`>= 8 chars`)
- Confirm password match
- Required field check via `required` HTML attribute
- File type validation via `react-dropzone`'s `accept` config

---

## 12. Environment & Config

### `.env` Variables (frontend)

```
VITE_API_URL=http://localhost:8000    # omit in production (nginx proxies /api)
```

All `VITE_*` vars are embedded at build time. Never put secrets here.

### Vite Dev Proxy

```ts
// vite.config.ts
proxy: {
  "/api": {
    target: "http://localhost:8000",
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, ""),
  },
}
```

In development, `fetch("/api/auth/login")` → proxied to `http://localhost:8000/auth/login`.

### Production Nginx Proxy

```nginx
location /api/ {
  proxy_pass http://backend:8000/;
  proxy_buffering off;    # required for SSE
  proxy_read_timeout 300s;
}
```

`proxy_buffering off` is critical — without it, SSE tokens are buffered and not streamed to the client.

---

## 13. Local Development

### Prerequisites

- Node 20+
- Running backend at `http://localhost:8000` (via `make dev-detach` or manually)

### Setup

```bash
cd frontend
npm install
npm run dev       # http://localhost:3000
```

### Useful Commands

```bash
npm run dev         # dev server with HMR + API proxy
npm run build       # production build to dist/
npm run typecheck   # tsc --noEmit (no emit, type check only)
npm run lint        # ESLint
npm run preview     # preview production build locally
```

---

## 14. Build & Deploy

### Docker Build

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
RUN npm run build           # outputs to dist/

# Stage 2: Serve
FROM nginx:alpine AS runner
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

### Production Checklist

- [ ] `VITE_API_URL` not set (nginx proxies `/api`)
- [ ] `nginx.conf` has `proxy_buffering off` (SSE)
- [ ] `try_files $uri $uri/ /index.html` (SPA fallback)
- [ ] `npm run build` passes without errors
- [ ] `npm run typecheck` passes
- [ ] `npm run lint` passes with 0 warnings

---

## 15. Testing Strategy

### Unit Tests (planned)

Test utilities and hooks with Vitest + Testing Library:

```
tests/
├── hooks/
│   └── useAuth.test.ts
├── utils/
│   └── formatDate.test.ts
└── components/
    └── CitationChip.test.tsx
```

### Component Tests (planned)

- `LoginPage` — submits form, shows error on failure, redirects on success
- `DocumentsPage` — renders upload zone, shows status badge, polls for updates
- `ChatPage` — sends message, renders streamed tokens, shows citation chips

### E2E Tests (planned)

Critical flows for Playwright:

1. Register → login → upload PDF → wait for ready → start chat → ask question → verify citation
2. Login → open previous session → verify messages load

---

## 16. Planned Enhancements

### Near-term

| Feature | Notes |
|---------|-------|
| Axios response interceptor for token auto-refresh | Call `/auth/refresh` on 401, retry original request |
| Toast notification system | Replace inline error banners with a global toast queue |
| Document search/filter | Filter document list by filename or status |
| Session delete from sidebar | Right-click or swipe-to-delete |
| Keyboard shortcuts | `Cmd+K` for new chat, `Esc` to close modal |

### Medium-term

| Feature | Notes |
|---------|-------|
| Dark mode toggle in sidebar | Wire `useDarkMode` into the UI |
| Paginated session history | Load more sessions as user scrolls |
| Citation highlight in source doc | Show the cited chunk in context of the full document |
| Multi-turn follow-up context | Include last N messages in the RAG prompt |
| Export session as Markdown | Download full conversation with citations |

### Long-term

| Feature | Notes |
|---------|-------|
| File preview panel | Render PDF inline using `pdfjs-dist` |
| Real-time status push | WebSocket instead of polling for document status |
| Collaborative sessions | Shared links to sessions (requires backend multi-user support) |
| Mobile-responsive layout | Current layout collapses sidebar on narrow screens |
