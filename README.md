# LionStudio — authorized cover worker

Background photo downloads for the existing LionStudio Mini App on GitVerse.
GitVerse hosted runners cannot reach Telegram; this public GitHub workflow downloads
only missing photos from exact catalog posts with the channel owner's permission.
No poster APIs, bot tokens, servers, Actions artifacts or paid runners.

The original 305 images stay in GitVerse. Only newly downloaded photos are retained here.
Images remain the property of their rights holders; no redistribution license is granted.
GitVerse reads the manifest and verifies post IDs, image bytes and SHA-256 before publishing.
All browser image requests still go to the existing GitVerse site.

Runs every six hours, before the corresponding GitVerse publication.
