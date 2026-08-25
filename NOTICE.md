## Modification Notice

This repository is a modified fork of [ai-dock/base-image](https://github.com/ai-dock/base-image), created by
Robert Ballantyne, trading as AI-Dock.

The code here has been changed from the original and this is not the upstream project. If
something in this fork misbehaves, please raise it here rather than with upstream.

What differs from the original, in summary:

- Modernization of the base OS and CUDA toolchain (Ubuntu 24.04, CUDA 12.6.3-cudnn-runtime),
  together with the Ubuntu 24.04 package and user-account changes that entails
- Dependency policy: floor pins and build-time SHA256 verification of downloaded artifacts
  in place of hard pins
- Correctness and hygiene fixes to the bundled service portal, `init.sh` and Caddy
  configuration — see the `PORT-*` commits
- CI workflow changes specific to this fork's container registry and build targets — see the
  `INFRA-*` commits

To review the complete diff against the original:

```
git remote add upstream https://github.com/ai-dock/base-image.git
git fetch upstream
git log --patch upstream/main..main
```

The original author's notice follows below, unaltered. Licence terms are in
[LICENSE.md](LICENSE.md).

---

## Notice:

I have chosen to apply a custom license to this software for the following reasons:

- **Uniqueness of Containers:** Common open-source licenses may not adequately address the nuances of software distributed within containers. My custom license ensures clarity regarding the separation of my code from bundled software, thereby respecting the rights of other authors.

- **Preservation of Source Code Integrity:** I am committed to maintaining the integrity of the source code while adhering to the spirit of open-source software. My custom license helps ensure transparency and accountability in my development practices.

- **Funding and Control of Distribution:** Some of the funding for this project comes from maintaining control of distribution. This funding model wouldn't be possible without limiting distribution in certain ways, ultimately supporting the project's mission.

- **Empowering Access:** Supported by controlled distribution, the mission of this project is to empower users with access to valuable tools and resources in the cloud, enabling them to utilize software that may otherwise require hardware resources beyond their reach.

I welcome sponsorship from commercial entities utilizing this software, although it is not mandatory. Your support helps sustain the ongoing development and improvement of this project.

You can sponsor this project at https://github.com/sponsors/ai-dock.

Your understanding and support are greatly appreciated.