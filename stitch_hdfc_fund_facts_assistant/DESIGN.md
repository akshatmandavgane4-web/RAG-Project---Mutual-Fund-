---
name: Luminous Finance
colors:
  surface: '#0d1511'
  surface-dim: '#0d1511'
  surface-bright: '#333b37'
  surface-container-lowest: '#08100c'
  surface-container-low: '#161d19'
  surface-container: '#1a211d'
  surface-container-high: '#242c28'
  surface-container-highest: '#2f3732'
  on-surface: '#dce5de'
  on-surface-variant: '#bacac1'
  inverse-surface: '#dce5de'
  inverse-on-surface: '#2a322e'
  outline: '#85948c'
  outline-variant: '#3c4a43'
  surface-tint: '#2fe0aa'
  primary: '#44edb7'
  on-primary: '#003828'
  primary-container: '#00d09c'
  on-primary-container: '#00533c'
  inverse-primary: '#006c4f'
  secondary: '#c4c6ce'
  on-secondary: '#2d3037'
  secondary-container: '#44474e'
  on-secondary-container: '#b3b5bd'
  tertiary: '#ffca7e'
  on-tertiary: '#442b00'
  tertiary-container: '#f5a814'
  on-tertiary-container: '#644100'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#59fdc5'
  primary-fixed-dim: '#2fe0aa'
  on-primary-fixed: '#002116'
  on-primary-fixed-variant: '#00513b'
  secondary-fixed: '#e1e2eb'
  secondary-fixed-dim: '#c4c6ce'
  on-secondary-fixed: '#191c22'
  on-secondary-fixed-variant: '#44474e'
  tertiary-fixed: '#ffddb1'
  tertiary-fixed-dim: '#ffba4b'
  on-tertiary-fixed: '#291800'
  on-tertiary-fixed-variant: '#624000'
  background: '#0d1511'
  on-background: '#dce5de'
  surface-variant: '#2f3732'
typography:
  headline-lg:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 14px
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  container-max: 1440px
  gutter: 1.5rem
  margin-desktop: 2.5rem
  margin-mobile: 1rem
  stack-sm: 0.5rem
  stack-md: 1rem
  stack-lg: 2rem
---

## Brand & Style
The design system focuses on a high-fidelity, premium financial experience that prioritizes data density and visual clarity. The brand personality is authoritative yet modern, utilizing a **Glassmorphic** approach to create depth within a sophisticated dark environment. 

The aesthetic is characterized by deep "ink" backgrounds contrasted against vibrant, neon-inflected accents. The user interface should evoke a sense of precision and high-performance, catering to serious investors who value speed and reliability. High-contrast elements ensure essential financial metrics are immediately legible, while subtle translucency and backdrop blurs provide a sense of layered architecture.

## Colors
The palette is built on a "Dark Onyx" foundation to reduce eye strain and allow the "Emerald" accent to command attention. 

- **Primary Emerald (#00D09C):** Used exclusively for growth indicators, primary actions, and brand touchpoints. 
- **Surface Layer (#171A20):** Applied to cards and containers with a 60% opacity alpha channel to enable glassmorphism.
- **Warning Amber (#FFB020):** Reserved for cautionary data, pending states, or neutral-to-downward market trends.
- **Primary Text (#F8FAFC):** High-contrast off-white for maximum readability against dark backgrounds.
- **Muted Text (#94A3B8):** Used for metadata, labels, and secondary information to maintain visual hierarchy.

## Typography
The system utilizes a dual-font strategy. **Outfit** is used for headlines and large data points to provide a geometric, modern character. **Inter** is used for all body text, tables, and labels to ensure maximum legibility and a systematic feel. 

Large numerical values (portfolio totals, stock prices) should use **Outfit SemiBold** with slightly tightened letter spacing to appear more robust. Labels and secondary captions should leverage Inter's medium weights to ensure they remain legible even when muted in color.

## Layout & Spacing
This design system uses a **Fluid Grid** model based on a 12-column structure for desktop and a 4-column structure for mobile. 

- **Grid:** 24px gutters provide ample breathing room between data-dense cards.
- **Rhythm:** An 8px base unit governs all padding and margin decisions. 
- **Adaptation:** On mobile, side margins shrink to 16px, and complex data tables should transition to a card-stack format or horizontal-scroll overflow to maintain readability. 
- **Density:** Financial dashboards require high information density; use `stack-sm` for related data points (label + value) and `stack-lg` to separate distinct functional sections.

## Elevation & Depth
Depth is achieved through **Glassmorphism** and subtle border treatments rather than traditional heavy shadows.

- **The Base:** The primary background (#0B0D10) sits at the lowest level.
- **The Glass Layer:** Cards and navigation bars use the surface color (#171A20) at 60% opacity with a `backdrop-filter: blur(12px)`.
- **Borders:** Every card must have a 1px solid border. Use `#FFFFFF` at 10% opacity to create a subtle "inner glow" or "rim light" effect that separates the card from the dark background.
- **Interactive States:** Hovering over a card should increase the border opacity to 20% and slightly lighten the background fill to 70% opacity.

## Shapes
The design system adopts a **Pill-shaped** philosophy for interactive elements to contrast against the structured, rectangular nature of the dashboard grid.

- **Interactive Elements:** Buttons, search bars, and toggle switches use the maximum radius (pill) to feel approachable and modern.
- **Containers:** Large data cards use a `rounded-xl` (1.5rem / 24px) radius to maintain a sophisticated balance between the fluid pill shapes and the screen edges.
- **Small Components:** Tags and chips should always be fully rounded.

## Components

### Buttons
- **Primary:** Pill-shaped, Emerald (#00D09C) background with Black (#0B0D10) text. No border.
- **Secondary:** Pill-shaped, transparent background with a 1px Emerald border.
- **Interaction:** On hover, primary buttons should have a soft Emerald outer glow (spread 10px, opacity 30%).

### Cards
- **Structure:** 24px internal padding, `rounded-xl` corners, 60% opacity surface with 12px backdrop blur.
- **Metrics:** Title in `label-sm` (muted), primary value in `headline-md` (primary text).

### Inputs
- **Field:** Pill-shaped, #171A20 background, 1px border at 10% white opacity.
- **Focus State:** Border color changes to Emerald (#00D09C).

### Lists & Tables
- **Rows:** Separated by a 1px border (#FFFFFF at 5% opacity). No alternating row colors.
- **Hover:** Active row highlights with a subtle 5% white overlay.

### Chips & Tags
- **Style:** Small, pill-shaped, with low-opacity background tints of the color they represent (e.g., a green "Buy" tag uses Emerald at 10% opacity background with 100% opacity Emerald text).