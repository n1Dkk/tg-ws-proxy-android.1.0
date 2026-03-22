# tg-ws-proxy-android

Android-oriented fork of `Flowseal/tg-ws-proxy` focused on running the proxy locally on Android through Termux, with a clean migration path toward a native APK implementation.

## What this fork is

This fork adapts the original `tg-ws-proxy` project for Android usage in a practical way:

- runs as a local SOCKS5 proxy on `127.0.0.1:1080`
- is intended to be launched from Termux on Android
- stores config and logs under `~/.config/tg-ws-proxy-android`
- provides an Android-specific launcher (`android.py`)
- keeps the original proxy core logic intact as much as possible
- documents a future path toward a native Android APK

This is **not** a native APK yet. It is a Termux-first Android fork.

## Status

Current state:

- Android/Termux launcher: implemented
- Local SOCKS5 proxy startup: implemented
- Android-friendly config/log paths: implemented
- Termux service/boot helpers: included
- Native Android APK: planned, not implemented in this fork

## Upstream project

Original upstream repository:

`Flowseal/tg-ws-proxy`

This fork is based on the upstream architecture where the proxy:

- listens locally on `127.0.0.1:1080`
- detects Telegram DC routing
- tunnels traffic over WebSocket/TLS where applicable
- falls back to direct TCP where needed

## Why this fork exists

The upstream project is structured primarily around desktop and cross-platform Python workflows. On Android, the main pain points are:

- no desktop tray/runtime model
- background execution limitations
- different config/log locations
- the need for a mobile-specific launcher and lifecycle
- difficulty of using desktop-oriented packaging directly on Android

This fork solves the practical Android runtime part first, without pretending to be a full mobile APK.

## Main differences from upstream

### Added

- `android.py` launcher
- Android-oriented package name and CLI entrypoint
- Android config and log path handling
- Termux helper scripts
- documentation for Android usage and APK migration

### Removed from the Android path

- desktop-first assumptions in the user flow
- tray-centered usage model
- desktop launch instructions as the primary setup path

### Preserved

- proxy core behavior from upstream
- local SOCKS5 flow
- DC handling logic
- WebSocket bridge behavior
- fallback behavior

## Repository layout

```text
contrib/     Helper scripts and service examples
docs/        Fork notes and roadmap
packaging/   Packaging-related files
proxy/       Core proxy logic inherited/adapted from upstream
android.py   Android/Termux launcher
linux.py     Upstream Linux launcher
macos.py     Upstream macOS launcher
windows.py   Upstream Windows launcher
```

## Requirements

Minimum practical runtime target:

- Android device
- Termux
- Python available in Termux
- Telegram client with SOCKS5 proxy support

Depending on environment, Python dependencies may require additional build packages.

## Installation (Termux)

Clone or copy the fork into device storage, then from Termux:

```bash
cd ~/storage/downloads/tg-ws-proxy-android
pip install -e .
```

If `cryptography` build fails on Android due to `maturin`, set the Android API level first:

```bash
export ANDROID_API_LEVEL=$(getprop ro.build.version.sdk)
pip install -e .
```

## First run

Initialize config:

```bash
tg-ws-proxy-android init
```

Show resolved config:

```bash
tg-ws-proxy-android show-config
```

Start proxy:

```bash
tg-ws-proxy-android start
```

Start proxy with wakelock:

```bash
tg-ws-proxy-android start --wake-lock
```

Open Telegram proxy link:

```bash
tg-ws-proxy-android open
```

## Telegram client setup

In Telegram Android, configure a SOCKS5 proxy:

- Server: `127.0.0.1`
- Port: `1080`
- Username: empty
- Password: empty

The proxy process must remain running in Termux while Telegram uses it.

## Runtime paths

Default Android/Termux paths:

- config: `~/.config/tg-ws-proxy-android/config.json`
- logs: `~/.config/tg-ws-proxy-android/proxy.log`

## Known limitations

### 1. This is not a native APK

The project currently runs through Termux and does not yet provide:

- Android UI
- Foreground service notification UI
- native background lifecycle
- `VpnService` integration

### 2. Background execution on Android is fragile

Android may suspend or kill long-running user processes unless they are managed carefully. Termux-based operation is useful for testing and niche deployment, but it is not equivalent to a production Android app.

### 3. Python/Rust dependency friction on Android

Some Python dependencies, especially `cryptography`, may need extra care on Android due to Rust/maturin/ABI specifics.

## Recommended usage

Use this fork when you want to:

- validate Android viability of the proxy logic
- run a local Telegram proxy on Android via Termux
- prepare for a later migration to a native mobile app

Do not treat this fork as the final APK product.

## Roadmap to native Android APK

Planned migration path:

### Phase 1 — Termux MVP

- Android launcher
- config handling
- local SOCKS5 proxy
- manual Telegram client configuration

### Phase 2 — Android app skeleton

- Kotlin project
- start/stop UI
- logs screen
- foreground service
- persistent settings

### Phase 3 — Native core integration

Possible options:

- port critical runtime to Kotlin
- port core to Go/Rust and bridge into Android
- replace Python runtime for production Android distribution

### Phase 4 — `VpnService`

Long-term goal:

- move away from manual proxy configuration where useful
- add Android-native traffic routing model
- improve background stability and UX

## Contribution notes

When contributing to this fork:

- preserve upstream proxy behavior where possible
- isolate Android-specific logic into launcher/runtime layers
- avoid unnecessary rewrites of the proxy core
- document any divergence from upstream clearly

## Syncing with upstream

Recommended strategy:

- keep Android-specific launcher and packaging isolated
- periodically rebase or merge upstream core changes
- resolve conflicts in `proxy/` conservatively
- document all Android-only patches in `docs/FORK_NOTES.md`

## License

This fork inherits the upstream license. See `LICENSE` for details.

## Disclaimer

This fork is provided for research, interoperability, and deployment experiments on Android-like environments. Native Android productization requires additional engineering work beyond this repository.
