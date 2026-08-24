"""Roman Numerals board game rules and move generation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

ROWS = 6
COLS = 5
VALUES = ["I", "II", "III", "IV", "V"]
STEPS = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}
DIRECTIONS = (
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1),
    (-1, -1),
    (-1, 1),
    (1, -1),
    (1, 1),
)

# 1-indexed rows from the rules PDF
BACK_ROWS = {1, 6}
FRONT_ORIGIN_ROWS = {2, 5}
CENTER_ROWS = {3, 4}


def _display_row(r: int) -> int:
    return r + 1


def initial_state() -> dict[str, Any]:
    pieces: list[dict[str, Any]] = []
    pid = 0
    for col, value in enumerate(VALUES):
        pieces.append(_piece(pid, 0, value, 0, col, origin_row=1))
        pid += 1
    for col, value in enumerate(VALUES):
        pieces.append(_piece(pid, 0, value, 1, col, origin_row=2))
        pid += 1
    for col, value in enumerate(VALUES):
        pieces.append(_piece(pid, 1, value, 4, col, origin_row=5))
        pid += 1
    for col, value in enumerate(VALUES):
        pieces.append(_piece(pid, 1, value, 5, col, origin_row=6))
        pid += 1
    return {
        "turn": 0,
        "winner": None,
        "win_reason": None,
        "unlocked": False,
        "pieces": pieces,
        "captured": [],
        "last_move": None,
    }


def _piece(
    pid: int, owner: int, value: str, r: int, c: int, origin_row: int
) -> dict[str, Any]:
    return {
        "id": pid,
        "owner": owner,
        "value": value,
        "r": r,
        "c": c,
        "origin_row": origin_row,
    }


def board_map(state: dict[str, Any]) -> dict[tuple[int, int], dict[str, Any]]:
    return {(p["r"], p["c"]): p for p in state["pieces"]}


def is_unlocked(state: dict[str, Any]) -> bool:
    """Back ranks (rows 1 and 6) unlock once every remaining front-line piece
    that started on row 2 or 5 sits on row 3 or 4."""
    fronts = [p for p in state["pieces"] if p["origin_row"] in FRONT_ORIGIN_ROWS]
    if not fronts:
        return True
    return all(_display_row(p["r"]) in CENTER_ROWS for p in fronts)


def piece_is_frozen(state: dict[str, Any], piece: dict[str, Any]) -> bool:
    if is_unlocked(state):
        return False
    return _display_row(piece["r"]) in BACK_ROWS


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < ROWS and 0 <= c < COLS


def legal_moves_for_piece(state: dict[str, Any], piece: dict[str, Any]) -> list[list[int]]:
    """A numeral may travel up to its value in any of eight directions,
    stopping before a friendly piece and capturing on an enemy square.
    """
    if piece_is_frozen(state, piece):
        return []
    occupied = board_map(state)
    steps = STEPS[piece["value"]]
    destinations: list[list[int]] = []
    for dr, dc in DIRECTIONS:
        for n in range(1, steps + 1):
            rr, cc = piece["r"] + dr * n, piece["c"] + dc * n
            if not in_bounds(rr, cc):
                break
            occupant = occupied.get((rr, cc))
            if occupant is None:
                destinations.append([rr, cc])
                continue
            if occupant["owner"] != piece["owner"]:
                destinations.append([rr, cc])
            break
    return destinations


def all_legal_moves(state: dict[str, Any], owner: int | None = None) -> list[dict[str, Any]]:
    if owner is None:
        owner = state["turn"]
    moves = []
    for piece in state["pieces"]:
        if piece["owner"] != owner:
            continue
        for dest in legal_moves_for_piece(state, piece):
            moves.append({"from": [piece["r"], piece["c"]], "to": dest, "id": piece["id"]})
    return moves


def apply_move(state: dict[str, Any], from_rc: list[int], to_rc: list[int]) -> dict[str, Any]:
    if state.get("winner") is not None:
        raise ValueError("The game is already over.")
    occupied = board_map(state)
    fr, fc = from_rc
    tr, tc = to_rc
    piece = occupied.get((fr, fc))
    if piece is None:
        raise ValueError("There is no piece on that square.")
    if piece["owner"] != state["turn"]:
        raise ValueError("It is not that player's turn.")
    legal = legal_moves_for_piece(state, piece)
    if [tr, tc] not in legal:
        raise ValueError("That move is not legal.")

    next_state = deepcopy(state)
    captured_here = None
    remaining = []
    for p in next_state["pieces"]:
        if p["id"] == piece["id"]:
            p["r"], p["c"] = tr, tc
            remaining.append(p)
        elif p["r"] == tr and p["c"] == tc:
            captured_here = p
        else:
            remaining.append(p)
    next_state["pieces"] = remaining
    if captured_here is not None:
        next_state["captured"].append(captured_here)

    next_state["last_move"] = {"from": [fr, fc], "to": [tr, tc], "id": piece["id"]}
    winner, reason = _check_winner(next_state, piece["owner"])
    next_state["winner"] = winner
    next_state["win_reason"] = reason
    if winner is None:
        next_state["turn"] = 1 - state["turn"]
        if not all_legal_moves(next_state):
            next_state["winner"] = piece["owner"]
            next_state["win_reason"] = "opponent has no legal moves"
    next_state["unlocked"] = is_unlocked(next_state)
    return next_state


def _check_winner(state: dict[str, Any], mover: int) -> tuple[int | None, str | None]:
    opponents = [p for p in state["pieces"] if p["owner"] != mover]
    if not opponents:
        return mover, "captured every opposing piece"

    goal_row = ROWS - 1 if mover == 0 else 0
    if any(p["owner"] == mover and p["r"] == goal_row for p in state["pieces"]):
        return mover, "reached the opposite back rank"
    return None, None


def public_state(state: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(state)
    out["unlocked"] = is_unlocked(state)
    out["frozen_ids"] = [p["id"] for p in state["pieces"] if piece_is_frozen(state, p)]
    return out


def choose_ai_move(state: dict[str, Any]) -> dict[str, Any] | None:
    moves = all_legal_moves(state)
    if not moves:
        return None
    occupied = board_map(state)
    scored: list[tuple[int, dict[str, Any]]] = []
    owner = state["turn"]
    goal_row = ROWS - 1 if owner == 0 else 0
    for move in moves:
        tr, tc = move["to"]
        piece = occupied[(move["from"][0], move["from"][1])]
        score = 0
        target = occupied.get((tr, tc))
        if target is not None:
            score += 40 + STEPS[target["value"]] * 4
        score += (5 - abs(tr - goal_row)) * 3
        score += STEPS[piece["value"]]
        # Prefer unlocking / staying unlocked
        trial = deepcopy(state)
        trial_piece = next(p for p in trial["pieces"] if p["id"] == piece["id"])
        trial_piece["r"], trial_piece["c"] = tr, tc
        trial["pieces"] = [
            p for p in trial["pieces"] if not (p["r"] == tr and p["c"] == tc and p["id"] != piece["id"])
        ]
        if is_unlocked(trial):
            score += 8
        scored.append((score, move))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]
