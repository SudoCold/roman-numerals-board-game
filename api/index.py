import os
import sys

from flask import Flask, jsonify, render_template, request

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from game import (  # noqa: E402
    all_legal_moves,
    apply_move,
    choose_ai_move,
    initial_state,
    legal_moves_for_piece,
    public_state,
    board_map,
)

app = Flask(
    __name__,
    template_folder=os.path.join(HERE, "templates"),
    static_folder=os.path.join(HERE, "static"),
)


def _error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/new")
def new_game():
    state = initial_state()
    return jsonify({"ok": True, "state": public_state(state)})


@app.post("/api/legal")
def legal():
    payload = request.get_json(silent=True) or {}
    state = payload.get("state")
    from_rc = payload.get("from")
    if not state or not from_rc:
        return _error("Missing state or origin square.")
    occupied = board_map(state)
    piece = occupied.get((from_rc[0], from_rc[1]))
    if piece is None:
        return _error("No piece on that square.")
    return jsonify(
        {
            "ok": True,
            "moves": legal_moves_for_piece(state, piece),
            "unlocked": public_state(state)["unlocked"],
            "frozen": piece["id"] in public_state(state)["frozen_ids"],
        }
    )


@app.post("/api/move")
def move():
    payload = request.get_json(silent=True) or {}
    state = payload.get("state")
    from_rc = payload.get("from")
    to_rc = payload.get("to")
    if not state or not from_rc or not to_rc:
        return _error("Missing state or move coordinates.")
    try:
        next_state = apply_move(state, from_rc, to_rc)
    except ValueError as exc:
        return _error(str(exc))
    return jsonify({"ok": True, "state": public_state(next_state)})


@app.post("/api/ai-move")
def ai_move():
    payload = request.get_json(silent=True) or {}
    state = payload.get("state")
    if not state:
        return _error("Missing state.")
    if state.get("winner") is not None:
        return jsonify({"ok": True, "state": public_state(state)})
    choice = choose_ai_move(state)
    if choice is None:
        return jsonify({"ok": True, "state": public_state(state)})
    try:
        next_state = apply_move(state, choice["from"], choice["to"])
    except ValueError as exc:
        return _error(str(exc))
    return jsonify({"ok": True, "state": public_state(next_state)})


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "moves_sample": len(all_legal_moves(initial_state()))})
