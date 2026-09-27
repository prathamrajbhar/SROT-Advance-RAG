# Design System: Enterprise Light

## Project: SROT (Advanced Multimodal Enterprise RAG)
**Document Version:** 1.0.0  
**Status:** Approved for Agile Execution  
**Theme:** Strict Enterprise Light (Clean, High-Density, Data-First, Professional)  

---

## 1. Design Philosophy & Aesthetic Core

Enterprise decision-makers, financial analysts, and legal teams distrust flashy, decorative "AI novelty" interfaces (e.g., purple/cyan glowing neon gradients, floating bubble chats, spinning rainbow sparkles, and low-density padding). 

SROT enforces a **Strict Enterprise Light Design System** modeled after premier analytical and developer infrastructure products (Stripe, Linear Light, Datadog, Snowflake, GitHub Enterprise):
1. **Utility & Information Density:** Maximize usable screen real estate. Use compact margins, high-density data tables, and structured split-pane layouts over sprawling empty cards.
2. **Monochromatic & Neutral Foundation:** 95% of the interface is built on crisp whites, cool slate/zinc neutrals, and sharp 1px borders. Color is reserved strictly for status semantics (Success, Warning, Error, Processing).
3. **Typography-Driven Hierarchy:** Clear contrast between dark charcoal text (`#0F172A`), muted slate metadata (`#64748B`), and clean monospace typography (`JetBrains Mono` / `SF Mono`) for code, timestamps, and citations.
4. **Interactive Rigor:** Every single interactive component must possess fully defined **Default, Hover, Focus-Visible, Active, Disabled, Loading, and Empty** states.

---

## 2. Color Palette & Semantic Tokens

### 2.1 Neutral Base Tokens
| Token Name | Hex Code | Tailwind Class | Application |
| :--- | :--- | :--- | :--- |
| `surface-bg` | `#FFFFFF` | `bg-white` | Main application background, document canvas |
| `surface-subtle` | `#F8FAFC` | `bg-slate-50` | Sidebar, split-drawer background, table headers |
| `surface-muted` | `#F1F5F9` | `bg-slate-100` | Code blocks, citation pill background, hover rows |
| `surface-card` | `#FFFFFF` | `bg-white` | Card container with 1px border |
| `border-subtle` | `#E2E8F0` | `border-slate-200` | Standard divider, card border, input border |
| `border-hover` | `#CBD5E1` | `border-slate-300` | Hover state for inputs and cards |
| `border-focus` | `#0F172A` | `border-slate-900` | Focus ring & active border |
| `text-primary` | `#0F172A` | `text-slate-900` | Headings, primary content, prompt inputs |
| `text-secondary`| `#475569` | `text-slate-600` | Descriptions, labels, secondary metadata |
| `text-muted` | `#64748B` | `text-slate-500` | Timestamps, file sizes, placeholders |
| `text-subtle` | `#94A3B8` | `text-slate-400` | Disabled text, breadcrumb separators |

### 2.2 Semantic Status Tokens (Muted & Functional)
| Status | Background | Border | Text | Icon / Application |
| :--- | :--- | :--- | :--- | :--- |
| **Success / Verified** | `#F0FDF4` (`bg-emerald-50`) | `#BBF7D0` (`border-emerald-200`) | `#166534` (`text-emerald-800`) | Verified citations, 100% indexed, connection healthy |
| **Warning / Processing**| `#FFFBEB` (`bg-amber-50`) | `#FDE68A` (`border-amber-200`) | `#92400E` (`text-amber-800`) | Ingestion underway, token warnings, rate limit alerts |
| **Error / Failed** | `#FEF2F2` (`bg-rose-50`) | `#FECACA` (`border-rose-200`) | `#991B1B` (`text-rose-800`) | Ingestion failure, invalid API key, DuckDB syntax error |
| **Info / Active** | `#F8FAFC` (`bg-slate-50`) | `#94A3B8` (`border-slate-400`) | `#0F172A` (`text-slate-900`) | Selected tab, active citation, neutral indicator |

---

## 3. Typography Scale & Font Rules

### 3.1 Font Families
- **Prose & UI:** `Inter`, `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `sans-serif`
- **Technical & Citations:** `JetBrains Mono`, `ui-monospace`, `SFMono-Regular`, `Menlo`, `monospace`

### 3.2 Type Scale
| Level | Font Size | Line Height | Weight | Tailwind |
| :--- | :--- | :--- | :--- | :--- |
| **Display Heading** | 24px (1.5rem) | 32px | Bold (700) | `text-2xl font-bold tracking-tight text-slate-900` |
| **Section Heading** | 18px (1.125rem)| 26px | SemiBold (600)| `text-lg font-semibold tracking-tight text-slate-900` |
| **Subheading** | 15px (0.9375rem)| 22px | Medium (500) | `text-[15px] font-medium text-slate-800` |
| **Body (Default)** | 14px (0.875rem)| 20px | Normal (400) | `text-sm leading-relaxed text-slate-700` |
| **Table / Dense UI**| 13px (0.8125rem)| 18px | Normal (400) | `text-[13px] leading-tight text-slate-700` |
| **Caption / Meta** | 12px (0.75rem) | 16px | Medium (500) | `text-xs text-slate-500` |
| **Monospace / Code**| 12px (0.75rem) | 18px | Normal (400) | `font-mono text-xs text-slate-800` |

---

## 4. Component Token Specifications

### 4.1 Buttons
- **Primary Button:**
  - Base: `bg-slate-900 text-white font-medium text-sm px-3.5 py-1.5 rounded-md shadow-sm border border-slate-900`
  - Hover: `hover:bg-slate-800 hover:border-slate-800`
  - Active: `active:bg-slate-950`
  - Focus: `focus-visible:ring-2 focus-visible:ring-slate-900 focus-visible:ring-offset-2 outline-none`
  - Disabled: `disabled:bg-slate-100 disabled:text-slate-400 disabled:border-slate-200 disabled:cursor-not-allowed`
- **Secondary / Outline Button:**
  - Base: `bg-white text-slate-700 font-medium text-sm px-3.5 py-1.5 rounded-md border border-slate-200 shadow-sm`
  - Hover: `hover:bg-slate-50 hover:text-slate-900 hover:border-slate-300`
  - Active: `active:bg-slate-100`
  - Focus: `focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-2 outline-none`
  - Disabled: `disabled:opacity-50 disabled:cursor-not-allowed`

### 4.2 Interactive Citation Chips (The Anchor Component)
Every citation in SROT is a high-density, clickable badge that triggers the split-view drawer:
- **PDF Citation:**
  `inline-flex items-center gap-1.5 px-2 py-0.5 rounded border border-slate-200 bg-slate-50 hover:bg-slate-100 hover:border-slate-300 text-xs font-mono text-slate-700 transition cursor-pointer`
  - Prefix Icon: `FileText` (12px)
  - Format: `[PDF: AnnualReport.pdf, P.14]`
- **Video Citation:**
  `inline-flex items-center gap-1.5 px-2 py-0.5 rounded border border-slate-200 bg-slate-50 hover:bg-slate-100 hover:border-slate-300 text-xs font-mono text-slate-700 transition cursor-pointer`
  - Prefix Icon: `PlayCircle` (12px)
  - Format: `[VID: Keynote.mp4 @ 04:12]`
- **Audio Citation:**
  `inline-flex items-center gap-1.5 px-2 py-0.5 rounded border border-slate-200 bg-slate-50 hover:bg-slate-100 hover:border-slate-300 text-xs font-mono text-slate-700 transition cursor-pointer`
  - Prefix Icon: `Volume2` (12px)
  - Format: `[AUD: EarningsCall.mp3 @ 12:45]`
- **Tabular / SQL Citation:**
  `inline-flex items-center gap-1.5 px-2 py-0.5 rounded border border-slate-200 bg-slate-50 hover:bg-slate-100 hover:border-slate-300 text-xs font-mono text-slate-700 transition cursor-pointer`
  - Prefix Icon: `Table` (12px)
  - Format: `[SQL: financials.xlsx, 4 Rows]`

### 4.3 Form Inputs & Secret Fields (BYOK)
- Base: `w-full bg-white border border-slate-200 rounded-md px-3 py-1.5 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900 transition shadow-sm`
- Secret Input: Monospace font, toggleable eye button (`Eye` / `EyeOff`), masked value `••••••••••••••••`.
- Health Check Status Pill:
  - Valid: `inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200`
  - Testing: `inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600 animate-pulse`
  - Error: `inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200`

### 4.4 Data Tables (Document Catalog & SQL Previews)
- Container: `border border-slate-200 rounded-lg overflow-hidden bg-white`
- Header: `bg-slate-50 border-b border-slate-200 px-3.5 py-2 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider`
- Rows: `border-b border-slate-100 last:border-b-0 hover:bg-slate-50/75 transition text-[13px] text-slate-700`
- Cells: `px-3.5 py-2.5 whitespace-nowrap`

---

## 5. Layout & Split-Pane Architecture

```
┌─────────────────┬──────────────────────────────────┬─────────────────────────────┐
│ Workspace Rail  │ Primary Chat & Synthesis View    │ Collapsible Citation Drawer │
│ (Width: 240px)  │ (Flexible, Max Width: 880px)     │ (Width: 480px - 640px)      │
│                 │                                  │                             │
│ • Documents     │ [User Query Prompt]              │ [Tab: PDF / Video / Data]   │
│ • Datasets      │                                  │                             │
│ • Onboarding    │ [Synthesized Answer]             │ [Live Media Player or PDF]  │
│ • Key Vault     │   ...as shown in [PDF: P.14]     │  Jump to: 04:12             │
│ • Analytics     │   and verified by [SQL Engine]   │                             │
│                 │                                  │ [Exact Chunk & Bounding Box]│
│                 │ [Input Prompt Bar]               │                             │
└─────────────────┴──────────────────────────────────┴─────────────────────────────┘
```

1. **Left Navigation Rail (240px):** Clean border-r (`border-slate-200`), logo, workspace switcher, nav items with 16px icons.
2. **Central Analytical Canvas:** Clean white canvas, centered maximum width (880px) for optimal reading comfort.
3. **Right Collapsible Split-Pane / Drawer (480px–640px):**
   - Automatically slides in when any citation chip is clicked.
   - Houses the active modality player (PDF page with bounding box, HTML5 video player, audio player, or DuckDB data grid).
   - Allows users to verify source integrity without leaving their analytical train of thought.

---

## 6. Accessibility & State Coverage (Zero Prototype Rules)

- **Contrast Ratios:** All text passes WCAG AA minimum 4.5:1 against its background.
- **Keyboard Navigation:** Full tab order across all buttons, inputs, citation chips, and tabs with visible focus rings.
- **Empty States:** Every view contains a crisp, non-cartoon empty state explaining what to do next (e.g. *"No documents uploaded. Drag a PDF, Excel, or Video file to begin ingestion."*).
- **Loading Skeletons:** Animated neutral shimmer (`bg-slate-100 animate-pulse`) matching exact component geometry during data fetches.
