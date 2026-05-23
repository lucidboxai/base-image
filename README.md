# lucidboxai/base-image

[![PR Build Check](https://github.com/lucidboxai/base-image/actions/workflows/pr-build-check.yml/badge.svg?branch=main)](https://github.com/lucidboxai/base-image/actions/workflows/pr-build-check.yml)

Base image for the **lucidboxai ai-dock stack** — a maintained fork of [ai-dock/base-image](https://github.com/ai-dock/base-image) modernized for current cloud GPU services. All lucidboxai images (`lucidboxai/python`, `lucidboxai/comfyui`) extend from this image.

## What this fork changes vs. upstream

The lucidboxai modernization (vs. dormant upstream as of late 2024):

| Component | Upstream `ai-dock` | `lucidboxai` |
|---|---|---|
| Ubuntu | 22.04 | **24.04** |
| CUDA base | 11.8 / 12.1 | **12.6.3-cudnn-runtime** |
| Python (in `lucidboxai/python`) | 3.10 | **3.12** (native, no PPA) |
| Build toolchain | Go 1.22, xcaddy 0.4.2, Node 22.2 | Go 1.26.3, xcaddy 0.4.5, Node 22.22.3 |
| FastAPI / uvicorn (serviceportal) | hard-pinned `==0.103` / `==0.23` | floor-pinned `>=0.115` / `>=0.34` |

A range of Ubuntu 24.04-specific fixes are folded in: native `unminimize`, `libgl1`/`plocate` (renamed packages), default `ubuntu` user removed to free UID 1000 for the runtime user, and a few drops (e.g. `rar`) for packages no longer in default 24.04 repos.

For the full pinned stack and the rules around bumping it, see [`lucidboxai/comfyui/COMPATIBILITY.md`](https://github.com/lucidboxai/comfyui/blob/main/COMPATIBILITY.md) — that file is the canonical compatibility reference for the whole lucidboxai stack.

## Documentation

Container behavior and environment variables shared with upstream are still documented in the [ai-dock base wiki](https://github.com/ai-dock/base-image/wiki). lucidboxai-specific deviations from those docs are tracked in this repo's commit history.

## Published images

Built via the `Docker Build` workflow (manual `workflow_dispatch`, ~18–20 min) and pushed to GHCR:

```
ghcr.io/lucidboxai/base-image:v2-cuda-12.6.3-cudnn-runtime-24.04
ghcr.io/lucidboxai/base-image:v2-cuda-12.6.3-base-24.04
ghcr.io/lucidboxai/base-image:v2-cuda-12.6.3-cudnn-devel-24.04
```

Browse all published tags at https://github.com/lucidboxai/base-image/pkgs/container/base-image.

> ROCm and CPU build variants are kept in the workflow matrix for parity with upstream but are not the production target; the lucidboxai stack focuses on the NVIDIA cudnn-runtime variant.

## Building locally

```sh
git clone https://github.com/lucidboxai/base-image.git
cd base-image
docker compose build
```

The image base, CUDA string, and tag are all set via `docker-compose.yaml` build args — override via env vars if you need a different variant.

## Publishing (maintainers)

```sh
gh workflow run docker-build.yml --repo lucidboxai/base-image
```

Then verify the new tag exists on GHCR. After base-image is republished, the build order for cascading changes through the stack is documented in `comfyui/COMPATIBILITY.md`: **base-image → python → comfyui**.

## Credits

This is a fork of [ai-dock/base-image](https://github.com/ai-dock/base-image) by [@robballantyne](https://github.com/robballantyne). Their original architecture, build scripts, Caddy + supervisor setup, and ai-dock common-base concept are the foundation this image builds on. Bug fixes and improvements that aren't fork-specific should ideally flow back upstream if/when ai-dock becomes active again.
