# Setup

1. Copy `scripts/render_profile_cards.py` into your profile repository.
2. Copy `.github/workflows/profile-cards.yml` into that same repository path.
3. Replace `README.md` with `README.template.md` (rename it to `README.md`).
4. In Settings → Actions → General, allow GitHub Actions read/write access to repository contents.
5. Push to `main`; the Action refreshes contribution JSON and cards daily.

## Local preview

```bash
python -m pip install "fonttools[woff]" brotli
GITHUB_TOKEN=YOUR_TOKEN python scripts/render_profile_cards.py
STATIC=1 GITHUB_TOKEN=YOUR_TOKEN python scripts/render_profile_cards.py
```

`STATIC=1` disables animations for screenshot previews. Set `PORTRAIT_URL` to an HTTPS portrait URL
if you want a portrait. Edit `REPOS` near the top of the script to change featured repositories.
The current README supplies the cyan brand colour (#00C2FF) and Fira Code styling.
