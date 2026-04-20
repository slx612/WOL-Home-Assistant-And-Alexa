# HACS publishing checklist

Use this checklist when preparing the repository for HACS publication and for
submission to the default HACS repository list.

## 1. Repository metadata on GitHub

Configure the repository `About` section on GitHub:

- Add a short description
- Add topics
- Keep issues enabled

Suggested topics:

- `home-assistant`
- `hacs`
- `custom-integration`
- `wake-on-lan`
- `windows`
- `alexa`

## 2. Validation workflows

Before asking for inclusion in the default HACS list:

- `HACS validation` must pass with no ignored checks
- `hassfest` must pass

## 3. Release

After the workflows are green:

1. Create a full GitHub release
2. Do not publish only a tag
3. Attach release notes

Suggested first release path:

- Start with a prerelease if the project has not yet been tested end to end on
  real hardware
- Promote to a normal release after the first successful real-world validation

## 4. HACS default repository submission

After the release exists:

1. Fork `hacs/default`
2. Add this repository to the `integration` list in alphabetical order
3. Open a PR from your fork
4. Wait for HACS review

Important:

- Default-list review can take a long time
- The project can already be installed before that as a normal HACS custom
  repository

## 5. Recommended before default-list submission

These are not strict HACS format requirements, but they are recommended for
this project before asking for broad public exposure:

- Real Home Assistant discovery test
- Real pairing-code test
- Real shutdown/restart test
- Real Wake-on-LAN boot test
- Real Alexa test through Home Assistant
