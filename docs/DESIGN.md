# Design Specification - Youtube AI Agent Agency

**Author:** Gemini (Frontend Designer)
**Version:** 1.0
**Status:** Draft

## 1. Design Principles
*   **Modern & Futuristic:** Reflecting "AI Agency" identity with glassmorphism and sleek dark mode.
*   **Data-Dense yet Clean:** Optimized for monitoring complex pipelines without clutter.
*   **Responsive:** Usable on Desktop (Primary) and Tablet.

## 2. Tech Stack (Frontend)
*   **Framework:** Next.js 14+ (App Router)
*   **Styling:** Tailwind CSS
*   **Components:** shadcn/ui (Radix UI based)
*   **Icons:** Lucide React
*   **State:** TanStack Query + Zustand

## 3. Visual Identity

### 3.1 Color Palette
*   **Primary:** `hsl(250, 95%, 65%)` (Vibrant Violet - AI Core)
*   **Secondary:** `hsl(340, 75%, 60%)` (Deep Pink - Youtube Energy)
*   **Background:** `hsl(240, 10%, 4%)` (Deep Space Black)
*   **Surface:** `hsl(240, 10%, 10%)` (Card Background)
*   **Text:**
    *   Primary: `hsl(0, 0%, 98%)`
    *   Muted: `hsl(240, 5%, 65%)`

### 3.2 Typography
*   **Font Family:** `Pretendard` (Korean), `Inter` (English/Numbers)
*   **Weights:** Regular (400), Medium (500), Bold (700)

## 4. UI Structure

### 4.1 Layout (Dashboard Layout)
*   **Sidebar (Left, Fixed, 250px)**
    *   Logo: "Youtube Agent"
    *   Nav Items:
        *   Dashboard (Home)
        *   Pipelines (List & Detail)
        *   Channels (Management)
        *   Settings (API Keys)
*   **Header (Top, Fixed, h-16)**
    *   Breadcrumbs
    *   Global Status Indicator (System Health)
    *   User Profile / Theme Toggle
*   **Main Content (Scrollable)**
    *   Padding: 24px
    *   Max-width: 1400px (Centered)

## 5. Key Pages & Components

### 5.1 Dashboard (`/`)
*   **Stats Cards:** Total Videos Uploaded, Active Pipelines, API Usage Cost.
*   **Recent Activity:** Table showing the last 5 pipeline executions with status pills (Success/Fail/Running).
*   **Quick Actions:** "Create New Video" button (Gradient primary).

### 5.2 Pipeline Builder (`/pipelines/new`)
*   **Input Form:**
    *   Topic / Keyword Input
    *   Channel Selector (Dropdown)
    *   Tone/Style Selector
*   **Preview:** Real-time validation of inputs.

### 5.3 Pipeline Details (`/pipelines/[id]`)
*   **Timeline Stepper:** Vertical step indicator for 6 agents (Research -> Script -> SEO -> Media -> Edit -> Publish).
*   **Live Logs:** Terminal-like view for real-time agent logs (WebSocket/Polling).
*   **Artifacts:** Tabs to view generated Script, Images, Video.

### 5.4 Channel Settings (`/channels`)
*   **Grid:** Cards for each connected YouTube channel.
*   **Status:** Token expiration warning, Quota usage.
*   **Add Channel:** OAuth flow trigger.

## 6. Implementation Guidelines for Claude-code
*   Use `flex` and `grid` for layout.
*   Maintain `gap-4` or `gap-6` consistency.
*   Use `shadcn/ui` components exclusively for consistency.
    *   Buttons, Cards, Badges, Tables, Dialogs.
*   All strict colors should use Tailwind CSS variables (`--primary`, `--background`).
