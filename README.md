# Roman Numerals

A two-player Flask board game based on the Roman-numeral movement rules. Pieces may move up to as many squares as their value (I–V), in any of the eight directions. Pieces on rows 1 and 6 cannot move until every remaining piece that started on rows 2 and 5 stands on row 3 or 4.

## Play locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5055](http://127.0.0.1:5055).

## Deploy on Vercel

1. Install the Vercel CLI and log in: `npm i -g vercel` then `vercel login`
2. From this folder run `vercel`
3. Accept the defaults. Vercel routes every request to the Flask app in `api/index.py`.

You can also import the Git repository in the [Vercel dashboard](https://vercel.com/new) and set the framework preset to Other. `requirements.txt` and `vercel.json` are already in place.
