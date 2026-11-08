# ViSign visual direction

## Brief and constraints

The user prefers gentle leaf green and wants improved decoration while preserving the overall camera/history layout. Keep camera inset/rounding, history behavior and keyboard shortcuts. Do not use generated character illustrations.

Later requested refinements: place guidance in the header centered over the camera; replace the idle camera icon with a ViSign wordmark, subtitle and raised start button; show white translation text on a transparent outlined panel; separate the translucent pause and camera-off buttons; shorten help to user actions.

## Reference study

- [Whereby Meetings](https://whereby.com/information/meetings): reference for a focused browser video workspace. Keep controls legible around the video surface.
- [Be My Eyes](https://www.bemyeyes.com/download-app/): reference for accessible assistance products and clear choices. Do not reproduce its layout or branding.
- [Fluent 2 color](https://fluent2.microsoft.design/color): neutral surfaces establish hierarchy, brand colors emphasize actions and selected states, and semantic status colors retain distinct meaning.
- Local `frontend-design` and `ui-ux-pro-max` skills: use deliberate surface hierarchy, semantic tokens, readable text contrast and restrained decoration. Automatic palette/layout suggestions were filtered against the user's existing layout and leaf-green preference.

## Final palette

| Role | Color |
| --- | --- |
| Page | `#f5f8f3` |
| History | `#ffffff` |
| Idle camera | `#eef5e9` |
| Text | `#284333` |
| Secondary text | `#596c5d` |
| Action | `#4e755a` |
| Selected history item | `#e0edda` |
| Divider | `#d6e2d3` |

Keep the existing font family and metrics. The camera and history remain exactly where they are. Use one short, static motion-arc motif at the camera's upper-right corner, sized independently of the container aspect ratio. Hide it during active video. Avoid a green tint on every surface, large waves behind the footer, glossy gradients, moving ornaments or extra content.

Implementation is scoped to `.app-shell` in `graphics.css`. `motion-arcs.svg` is decorative vector artwork, not an actual detection overlay. The earlier corner/page wave assets are retained but are no longer used by the theme.

Verification compares bounds, font metrics and spacing at 1440×900, 375×812, 640×360 and 320×180; active-camera and accessibility checks use synthetic camera input.
