# LionStudio — authorized cover worker

Background photo downloads for the existing LionStudio Mini App on GitVerse.
GitVerse hosted runners cannot reach Telegram; this public GitHub workflow downloads
only missing photos from exact catalog posts with the channel owner's permission.
No poster APIs, bot tokens, servers, Actions artifacts or paid runners.

The original 305 images stay in GitVerse. Only newly downloaded photos are retained here.
Images remain the property of their rights holders; no redistribution license is granted.
GitVerse reads the manifest and verifies post IDs, image bytes and SHA-256 before publishing.
All browser image requests still go to the existing GitVerse site.

Runs every six hours. The prepared publication bridge pushes only
`.publish-request.json` to GitVerse master, using an isolated Git index and a
normal fast-forward push. It preserves the latest application code and excludes
the worker's dirty files. GitVerse then builds and publishes through its existing
workflow. GitHub fails if the live date and all five hashed runtime files do not
confirm publication within eight minutes.

Activation requires the owner's explicit approval: create a dedicated write
deploy key for GitVerse **NemoBek/lionstudio-3d only**, and store its private part
as the GitHub **NemoBek/lionstudio-3d-covers** secret `GITVERSE_DEPLOY_KEY`.
Never commit the private key. The worker writes it to a temporary file with mode
0600 and removes the file after the push. SSH verifies the pinned official host
key in `gitverse_known_hosts`, fingerprint
`SHA256:IL4khwaSrT4uHCu9LTUW7dRJyMB5XkOJnFrP0nmdMXU`.

Official references:
- https://gitverse.ru/docs/collaborative/authentification/deploy-keys/
- https://gitverse.ru/docs/collaborative/authentification/gitverse-ssh-key-fingerprints/

The owner approved this repository-scoped persistent key on 14 November 2026.
The dedicated key is installed and its private part is stored only in the
repository Actions secret. Publication is verified by the workflow's live check.
