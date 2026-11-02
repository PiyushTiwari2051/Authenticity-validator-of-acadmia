# Owner Decisions Record - Frontend & Design System

Date: 2026-11-01
Status: Proceeding on formal baseline assumptions to deliver the complete working system.

Pursuant to Section 13.7 of the Frontend & Design Brief, the operational decisions are recorded below:

1. **Product Name & Logo**:
   - Working Name: **Sanad** (प्रमाणन).
   - Selected Logo: **Option 1** — The wordmark "Sanad" in Fraunces serif with an integrated mathematical rosette mark.
2. **Palette and Typography**:
   - Palette: **"Paper" light theme** (`#FAF6EC` background, `#15191F` ink, `#1F2F5C` neel, `#C2412D` sindoor) and **"Night press" dark theme** (`#0F1318` background, `#ECE7DA` paper text).
   - Typography: Fraunces (variable serif) for headings, Public Sans for UI, IBM Plex Mono for IDs/hashes, and Noto Devanagari for Hindi.
3. **Bilingual Scope & Review**:
   - English and Hindi (`en`, `hi`) message catalogs are loaded from commit one. Starting strings follow Section 10.3 plain everyday Hindi guidelines.
4. **Institutional Logos**:
   - Version 1 supports optional institution logos displayed inside the designed certificate sheet, labeled as "Provided by institution".
5. **Performance Testing**:
   - Lighthouse CI runs with 4x CPU throttle mobile profile against local Caddy/Next.js bundle.
6. **Sample Certificate Persona**:
   - Uses realistic synthetic persona: "Rohan Sharma" at "Demo Institute of Technology (sample, not a real institution)".
