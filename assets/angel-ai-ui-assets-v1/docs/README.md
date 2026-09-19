# Angel AI UI Asset Pack v1

This pack contains reusable visual assets and design tokens for implementing the Angel AI dark neon-blue chat interface.

## Included

- `images/angel-ai-reference.png`: complete supplied reference image
- `images/angel-ai-header-mark.png`: header logo crop from the reference
- `images/angel-ai-small-mark.png`: assistant message mark crop
- `images/user-avatar.png`: user avatar crop
- `images/online-status-area.png`: online status reference crop
- `icons/*.svg`: scalable starter assets
- `design-tokens.json`: colors, layout, and theme values

## Implementation notes

The reference screenshot is a visual target, not a production UI layer. The application should recreate the interface with native UI widgets, reusable components, accessible labels, keyboard navigation, responsive layout behavior, and real data bindings.

Recommended implementation order:

1. App shell and dark theme
2. Sidebar navigation
3. Chat message components
4. Confirmation/action cards
5. Composer and toolbar
6. Settings theme selector
7. Angel Nexus integration panel
8. Accessibility and resize testing

## Angel Nexus UI Assets (v2)

Added reference assets for the Angel Nexus dashboard:
- `images/angel-nexus-reference.png` — full dashboard reference
- `images/angel-nexus-header-reference.png` — header reference crop
- `images/angel-nexus-hero-banner.png` — hero/banner reference crop
- `images/angel-nexus-dashboard-reference.png` — dashboard content reference crop

Design direction:
- Dark navy/black surfaces
- Neon blue borders and highlights
- Cyan, green, purple, and amber status accents
- Rounded cards with subtle glow
- Left navigation rail
- Dashboard cards, quick actions, recent activity, system overview, and module categories

These images are visual references for implementation. They are not a substitute for live UI components or functional module logic.

## Generic User Avatar

Added `images/user-avatar-template.svg`.

Implementation behavior:
- Replace `{{INITIAL}}` with the first letter of the user's display name.
- Convert the initial to uppercase.
- Use `U` as a fallback when no display name is available.
- Keep the avatar generic and privacy-friendly without requiring a profile photo.
