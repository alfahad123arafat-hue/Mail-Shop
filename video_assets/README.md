# Mail-Shop cartoon tutorial

`mail_shop_tutorial_5min.mp4` is a finished 5-minute, 1280×720 cartoon explainer for the Mail-Shop workspace.

- **Format:** MP4, H.264 video + AAC audio
- **Duration:** 04:59.99
- **Voice:** Bangla narration with English product terms
- **Visual style:** clean 2D vector-like cartoon scenes
- **Chapters:** welcome, account connection, Inbox, OTP Vault, and privacy-first Settings

The video uses only original vector illustrations and synthetic narration. The sample email addresses, counts, and OTP shown in the illustrations are fictional UI examples; no customer data is included.

## Source files

- `mail_shop_tutorial_5min.mp4` — shareable deliverable
- `mail_shop_tutorial_script.txt` — narration script
- `audio/` — chapter narration clips
- `scenes/` — 15 rendered storyboard frames
- `render_scenes.py` — deterministic Pillow scene renderer
- `build_video.py` — ffmpeg build script

To rebuild in the sandbox after installing `Pillow` and `imageio-ffmpeg` into `/tmp/mail_shop_tools`:

```bash
PYTHONPATH=/tmp/mail_shop_tools python3 video_assets/render_scenes.py
python3 video_assets/build_video.py
```
