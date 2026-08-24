"""Local entrypoint. On Vercel the app is served from api/index.py."""

from api.index import app

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5055, debug=True)
