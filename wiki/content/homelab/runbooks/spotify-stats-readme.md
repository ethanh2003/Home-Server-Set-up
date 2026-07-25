# spotify-stats/README.md

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

# Your Spotify

This stack builds Your Spotify from a pinned upstream checkout because the live
server carries three small import-performance fixes.

Bootstrap the build context before the first deployment:

```bash
git clone https://github.com/Yooooomi/your_spotify.git upstream-your_spotify
git -C upstream-your_spotify checkout 641af14a8e32c871b5de652364707987ea1d9df8
git -C upstream-your_spotify apply ../patches/your-spotify-local.patch
docker compose build
docker compose up -d
```

Runtime credentials belong in `.env`; do not commit that file. MongoDB data is
stored in the `spotify-stats_mongo_data` named volume and is covered by the
application-consistent export job.
