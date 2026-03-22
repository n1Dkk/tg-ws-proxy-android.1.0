# Fork Notes

## Summary

This fork adapts `tg-ws-proxy` for Android usage through Termux and serves as a stepping stone toward a native APK implementation.

## Fork goals

1. Make the upstream proxy usable on Android with minimal changes to core logic.
2. Separate Android-specific launcher/runtime behavior from the inherited proxy code.
3. Create a stable baseline for future APK work.

## What changed

### Android launcher

Added `android.py` to provide:

- Android-specific CLI entrypoint
- config initialization
- log path discovery
- helper command to open `tg://socks?...`
- Android/Termux-friendly startup messages

### Packaging

Added/updated packaging metadata so the project can expose an Android-oriented command:

- `tg-ws-proxy-android`

### Paths

Standardized runtime paths for Android/Termux:

- config directory under `~/.config/tg-ws-proxy-android`
- dedicated log file under the same directory

### Service helpers

Included helper scripts under `contrib/` for:

- Termux service integration
- boot-time startup examples

## What did not change

The fork intentionally avoids rewriting the core proxy logic at this stage. The following remain conceptually aligned with upstream:

- local SOCKS5 listener
- Telegram DC routing behavior
- WebSocket bridge logic
- direct TCP fallback behavior

## Rationale

A full native APK requires a different runtime model:

- Android foreground service
- Android lifecycle handling
- persistent notification
- optional `VpnService`
- likely replacement of Python runtime in production

That work is larger than a straightforward fork patch. This fork therefore focuses on the shortest path to a usable Android deployment.

## Risks and caveats

### Dependency friction

Some Python packages may be difficult to build on Android, especially when Rust-backed wheels are involved.

### Background process reliability

Termux processes can be interrupted by Android battery and process management policies.

### Localhost assumptions

The approach assumes Telegram Android can use a local SOCKS5 proxy reliably on `127.0.0.1:1080`.

## Suggested branch strategy

Recommended branches:

- `main`: stable Android/Termux fork
- `upstream-sync`: periodic sync from upstream
- `apk-prototype`: native Android app skeleton and experiments
- `vpnservice`: future Android-native routing work

## Suggested GitHub repository description

> Android-oriented fork of tg-ws-proxy for Termux-based local Telegram SOCKS5 proxying, with a migration path toward a native APK.

## Suggested GitHub topics

- telegram
- socks5
- proxy
- websocket
- android
- termux
- python
- mtproto

## Release recommendations

For GitHub releases, publish:

- source archive of the fork
- patch relative to upstream
- short changelog of Android-specific changes
- installation notes for Termux users

## Next documentation to add

Recommended future docs:

- `docs/TERMUX.md`
- `docs/TROUBLESHOOTING.md`
- `docs/APK-ROADMAP.md`
- `docs/UPSTREAM-SYNC.md`

## Maintainer note

If the project direction shifts fully to APK, keep this fork as a compatibility branch and start the native mobile app as a sibling project or dedicated branch to avoid mixing desktop/Termux and Android-native concerns too early.
