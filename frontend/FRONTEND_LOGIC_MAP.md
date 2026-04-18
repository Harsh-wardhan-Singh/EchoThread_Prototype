# Frontend Logic Map (EchoThread)

This document maps the logic in each file under `frontend/`.

---

## Root / Tooling Files

### `package.json`
- Defines project metadata and ESM mode (`"type": "module"`).
- Scripts:
  - `dev`: starts Vite dev server.
  - `build`: builds production bundle.
  - `lint`: runs ESLint on project files.
  - `preview`: serves production build locally.
- Runtime dependencies provide:
  - UI/runtime (`react`, `react-dom`), routing (`react-router-dom`), HTTP (`axios`), charting (`chart.js`, `react-chartjs-2`).
- Dev dependencies define linting, Tailwind/PostCSS, and Vite plugin setup.

### `vite.config.js`
- Uses `defineConfig` with `@vitejs/plugin-react`.
- No custom alias/proxy/build overrides; default Vite behavior plus React plugin.

### `tailwind.config.js`
- Tailwind content scanning includes `index.html` and all source files in `src/**/*.{js,jsx,ts,tsx}`.
- Theme extension is empty (`extend: {}`), so default Tailwind tokens are used.
- No extra Tailwind plugins configured.

### `postcss.config.js`
- Enables Tailwind PostCSS plugin (`@tailwindcss/postcss`) and `autoprefixer`.
- This pipeline processes utility classes and adds vendor prefixes in build/dev.

### `eslint.config.js`
- Flat ESLint config for JS/JSX files.
- Extends recommended JS rules + React hooks + React refresh config.
- Browser globals enabled.
- Adds `no-unused-vars` rule with uppercase ignore pattern for symbols like constants/components.
- Ignores `dist` output.

### `index.html`
- Minimal Vite HTML shell.
- Mount target: `<div id="root"></div>`.
- Loads client app via module script `/src/main.jsx`.

### `README.md`
- Default Vite React template documentation.
- Informational only; no runtime app logic.

---

## Public Assets

### `public/favicon.svg`
- Static icon asset served by Vite.
- No application logic.

### `public/icons.svg`
- Static SVG asset file.
- No application logic.

---

## Source Entry and Global Styles

### `src/main.jsx`
- Application entry point.
- Imports global CSS (`index.css`) and root component (`App.jsx`).
- Mounts app to DOM root with `createRoot`.
- Wraps app in `StrictMode` to surface potential React issues in development.

### `src/index.css`
- Imports Tailwind layers:
  - `@tailwind base;`
  - `@tailwind components;`
  - `@tailwind utilities;`
- Defines global `body` styling (gradient background, text color, font smoothing).
- Note: current file contains `@tailwind utilities;z` (extra `z`) which appears to be a typo.

---

## App Shell and Routing

### `src/App.jsx`
- Central routing and authentication gatekeeper.
- Imports page-level routes: `Login`, `Diary`, `Feed`, `PulseDashboard`, `CounselorDashboard`.
- `ProtectedRoute` logic:
  - If no role or role not allowed, redirects to `/`.
  - Otherwise renders child route element.
- Auth state logic:
  - Initializes from `localStorage` (`role`, `email`).
  - `onLogin(role, email)` persists values to localStorage and updates React state.
  - `onLogout()` clears localStorage and resets auth state.
- Builds `authProps` with `useMemo` and passes shared auth/logout props to protected pages.
- Route map:
  - `/` → `Login`
  - `/diary`, `/feed`, `/pulse` → student-only
  - `/counselor` → counselor-only
  - wildcard `*` → redirect to `/`
- Also includes visual layout wrappers around `<Routes>` for app-level background/card framing.

---

## Pages

### `src/pages/Login.jsx`
- Handles OTP-based login flow.
- Local state:
  - `email`, `otp`
  - `otpRequested` (toggles OTP input area)
  - `info`, `error` messages
  - `loading` submit state
- `handleSendOtp`:
  - Clears error, sets optimistic info (`OTP sent`), and marks OTP UI as requested.
  - Calls `sendOtp(email)`; on failure still keeps optimistic info message.
- `handleVerify`:
  - Prevents default submit.
  - Calls `verifyOtp(email, otp)`.
  - On success:
    - calls parent `onLogin(result.role, result.email)`
    - role-based navigation (`/counselor` for counselor, else `/diary`).
  - On failure: sets authentication error.
  - Uses `finally` to stop loading state.
- Rendering logic:
  - OTP input appears with animated expand/collapse controlled by `otpRequested`.
  - Submit button label changes with loading state.
  - Info and error banners are conditionally rendered.

### `src/pages/Diary.jsx`
- Student diary entry page.
- Local state:
  - `text` for textarea input
  - `result` for analysis output
  - `loading` for submit state
- `handleAnalyze`:
  - Prevents submit default.
  - Skips empty/whitespace-only entries.
  - Calls `analyzeDiary(email, text.trim())`.
  - Stores backend analysis response in `result`.
  - Clears textarea after successful save/analyze.
  - Stops loading in `finally`.
- Composition:
  - Shows `Navbar` with role/logout.
  - Shows `MoodTracker` with latest `result`.

### `src/pages/Feed.jsx`
- Anonymous community feed page for students.
- Local state:
  - `posts` list
  - `content` for new post textarea
  - `loading` for post submission
- Load logic (`useEffect`):
  - Fetches posts once at mount with `getPosts()`.
  - Uses `mounted` flag to avoid state updates after unmount.
- `handleCreate`:
  - Prevents default submit.
  - Skips empty content.
  - Calls `createPost(content.trim())`.
  - Clears input on success.
  - Re-fetches posts to show latest server state.
  - Uses `finally` to stop loading.
- Rendering:
  - Top composer form.
  - Post list rendered via `PostCard` per post.

### `src/pages/PulseDashboard.jsx`
- Student pulse analytics view.
- Local state: `pulse` object (`null` until loaded).
- Load logic (`useEffect`):
  - Calls `getPulse()` once on mount and stores result.
- Conditional rendering:
  - While `pulse` is null, shows loading message with navbar.
  - After load, shows metrics and chart.
- Metric display:
  - Uses inner `Metric` component to render labeled values.
  - Reads from `pulse.total_posts`, `pulse.total_diary_entries`, sentiment/risk distributions.
- Chart:
  - Passes `pulse.seven_day_activity` into `PulseChart`.

### `src/pages/CounselorDashboard.jsx`
- Counselor-only dashboard for flagged posts.
- Local state: `posts` list.
- Load logic (`useEffect`):
  - Calls `getFlaggedPosts()` once on mount.
  - Stores resulting list.
- Rendering behavior:
  - Displays cards with risk badge, post content, sentiment/emotion summary.
  - Includes a local textarea per card for drafting counselor response (UI-only; no submit handler yet).
  - Shows fallback empty-state message when no flagged posts exist.

---

## Components

### `src/components/Navbar.jsx`
- Shared top navigation and role-dependent nav links.
- `NavLink` subcomponent:
  - Uses `useLocation()` to determine active route (`location.pathname === to`).
  - Applies active/inactive styling based on route match.
- `Navbar` logic:
  - Always shows role tag and logout button (`onLogout`).
  - If role is `student`, shows bottom fixed nav tabs to `/diary`, `/feed`, `/pulse`.
  - If role is `counselor`, shows single nav link to `/counselor`.

### `src/components/PostCard.jsx`
- Displays one post with metadata and optional comments.
- Logic:
  - Safely derives formatted local date from `post.created_at`.
  - Coerces `post.comments` to array fallback.
  - Conditionally renders comment block only when comments exist.
- Pure presentational component (no local state/effects).

### `src/components/MoodTracker.jsx`
- Shows analysis summary from diary AI result.
- Behavior:
  - Returns `null` if no `result` provided.
  - Maps known `result.emotion` values to predefined supportive summary text.
  - Falls back to a generic message for unknown emotion values.
  - Displays `sentiment`, `emotion`, and `risk` from result.
- Pure render component with computed text; no network calls.

### `src/components/PulseChart.jsx`
- Bar chart wrapper around `react-chartjs-2`.
- Setup logic:
  - Registers required Chart.js modules (`CategoryScale`, `LinearScale`, etc.).
  - Converts `activity` array into `labels` and `values`.
  - Creates `data` + `options` objects for chart rendering.
- Defaults `activity` prop to empty array to avoid runtime failures.
- Renders one `<Bar>` chart titled `7-Day Campus Activity`.

---

## Data and API Layer

### `src/data/mockData.js`
- Provides fallback mock payloads used when backend APIs fail.
- Exports:
  - `mockPosts`: sample feed entries with computed timestamps.
  - `mockPulse`: sample metrics, distributions, top emotions, and 7-day activity.
- Supports resilient UI in offline/unavailable-backend scenarios.

### `src/services/api.js`
- Central API abstraction over Axios.
- Axios client config:
  - `baseURL`: `VITE_API_URL` env var or default `http://127.0.0.1:8000`.
  - `timeout`: 5000ms.
- Methods:
  - `sendOtp(email)` → POST `/auth/send-otp`.
  - `verifyOtp(email, otp)` → POST `/auth/verify-otp`.
  - `analyzeDiary(email, text)` → POST `/ai/diary`.
  - `createPost(content)` → POST `/posts`.
  - `getPosts()` → GET `/posts`, fallback to `mockPosts` on error.
  - `getFlaggedPosts()` → GET `/posts/flagged`, fallback to empty list on error.
  - `getPulse()` → GET `/pulse`, fallback to `mockPulse` on error.
- This file contains all frontend network endpoint mappings and error fallback policy.

---

## End-to-End Frontend Logic Flow (High-Level)

1. App boots from `main.jsx` and mounts `App`.
2. `App` restores auth from localStorage and controls route access.
3. User logs in via `Login` (`sendOtp` + `verifyOtp`), then role-based navigation occurs.
4. Student path:
   - `Diary` saves/analyzes text via `/ai/diary` and displays `MoodTracker`.
   - `Feed` fetches/creates anonymous posts via `/posts`.
   - `PulseDashboard` fetches pulse metrics via `/pulse` and visualizes with `PulseChart`.
5. Counselor path:
   - `CounselorDashboard` reads `/posts/flagged` and displays support workflow UI.
6. `Navbar` provides role-based navigation and logout across protected views.
