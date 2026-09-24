# WakeLink guides and brand implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make WakeLink's current installation and Alexa instructions understandable in English and Spanish, with consistent visible icons and names.

**Architecture:** Keep legacy integration/Windows IDs for upgrade compatibility. Reuse the existing Windows icon source for tray and Home Assistant branding. Make current docs short and separate archived beta records.

**Tech Stack:** Python, Pillow, Home Assistant custom integration, NSIS, Markdown.

**Spec:** User-approved scope in this task: matching icons, beginner Alexa instructions, multilingual documentation and cleanup.

## Global Constraints

- Never reset pairing, credentials, config entries or existing certificates during an update.
- Never create a Home Assistant access token, pair Alexa or send a PC power command during development.
- English and Spanish are both first-class supported languages.
- Matterbridge and its Home Assistant plugin remain explicit external dependencies; never claim Alexa is validated without hardware evidence.

## Review Focus

- An existing beta.10 Windows installation must still discover the new installer through the old asset name.
- Existing HACS installations must keep the `pc_power_free` domain.
- The tray icon must load from a PyInstaller bundle, not only from a source checkout.
- A Matterbridge plugin with no filter could expose unrelated devices; warn before pairing.
- Historical beta documents must not masquerade as current instructions.

### Task 1: Shared branding and visible names

**Files:** `windows_agent/build_assets.py`, `windows_agent/pc_power_tray.py`, packaging scripts/spec, `brand/*`, `windows_agent/desktop_ui.py`, tests.

- [x] Write tests for common icon pixels and bundled tray asset; confirm red.
- [x] Generate Home Assistant images from the Windows symbol, load that symbol in the tray and bundle it.
- [x] Fix remaining visible old app names; run targeted tests and inspect images.

### Task 2: Current bilingual installation and Alexa guides

**Files:** `README.md`, `docs/README.es.md`, new `docs/GETTING_STARTED.*.md`, `docs/ALEXA.*.md`, `docs/README.md`, wizard translations, tests.

- [x] Add tests for current links, guide language parity, and exact disclaimer; confirm red.
- [x] Write concise current guides, with direct wizard link and safe Matterbridge/Alexa sequence.
- [x] Mark version-specific documents as historical without destroying their records; run guide tests.

### Task 3: Package and release verification

**Files:** version metadata, release build output, package verification tests.

- [x] Build and inspect Windows installer and HACS integration ZIP; run full tests.
- [x] Check upgrade-compatible filenames and no user-data changes.
- [ ] Publish a prerelease only if all checks and artifact preparation pass; otherwise state the exact remaining gap.
