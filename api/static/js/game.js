const boardEl = document.getElementById("board");
const statusEl = document.getElementById("status");
const lockEl = document.getElementById("lock");
const messageEl = document.getElementById("message");
const modeEl = document.getElementById("mode");
const captured = {
  0: document.getElementById("captured-0"),
  1: document.getElementById("captured-1"),
};

let state = null;
let selected = null;
let hints = [];
let busy = false;

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json();
  if (!data.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

function occupantAt(r, c) {
  return state.pieces.find((p) => p.r === r && p.c === c);
}

function render() {
  boardEl.innerHTML = "";
  const last = state.last_move;
  for (let r = 0; r < 6; r += 1) {
    for (let c = 0; c < 5; c += 1) {
      const square = document.createElement("button");
      square.type = "button";
      square.className = `square ${(r + c) % 2 === 0 ? "light" : "dark"}`;
      square.dataset.r = String(r);
      square.dataset.c = String(c);

      if (last && last.from[0] === r && last.from[1] === c) square.classList.add("last");
      if (last && last.to[0] === r && last.to[1] === c) square.classList.add("last");
      if (selected && selected[0] === r && selected[1] === c) square.classList.add("selected");

      const hint = hints.find((h) => h[0] === r && h[1] === c);
      if (hint) {
        square.classList.add("hint");
        if (occupantAt(r, c)) square.classList.add("capture");
      }

      const piece = occupantAt(r, c);
      if (piece) {
        const token = document.createElement("div");
        token.className = `piece owner-${piece.owner}`;
        token.textContent = piece.value;
        if (state.frozen_ids.includes(piece.id)) token.classList.add("frozen");
        square.appendChild(token);
      }

      square.addEventListener("click", () => onSquare(r, c));
      boardEl.appendChild(square);
    }
  }

  const names = ["Gold", "Crimson"];
  if (state.winner !== null && state.winner !== undefined) {
    statusEl.textContent = `${names[state.winner]} wins`;
    messageEl.textContent = `Victory by ${state.win_reason}.`;
  } else {
    statusEl.textContent = `${names[state.turn]} to move`;
  }

  lockEl.textContent = state.unlocked ? "Back ranks open" : "Back ranks locked";
  lockEl.classList.toggle("open", Boolean(state.unlocked));

  for (const owner of [0, 1]) {
    const taken = state.captured.filter((p) => p.owner === owner);
    captured[owner].innerHTML = taken.length
      ? taken.map((p) => `<span>${p.value}</span>`).join("")
      : "<span>—</span>";
  }
}

async function onSquare(r, c) {
  if (busy || state.winner !== null) return;
  if (modeEl.value === "ai" && state.turn === 1) return;

  const piece = occupantAt(r, c);
  if (selected && hints.some((h) => h[0] === r && h[1] === c)) {
    await playMove(selected, [r, c]);
    return;
  }

  if (!piece || piece.owner !== state.turn) {
    selected = null;
    hints = [];
    render();
    return;
  }

  try {
    const data = await api("/api/legal", {
      method: "POST",
      body: JSON.stringify({ state, from: [r, c] }),
    });
    selected = [r, c];
    hints = data.moves;
    if (data.frozen) {
      messageEl.textContent =
        "This back-rank piece is sealed until every remaining II/V-rank piece stands on rows 3 and 4.";
    } else if (!hints.length) {
      messageEl.textContent = "No legal landing squares for that numeral.";
    } else {
      messageEl.textContent = `${piece.value} may travel up to ${
        { I: 1, II: 2, III: 3, IV: 4, V: 5 }[piece.value]
      } square(s) in any direction.`;
    }
    render();
  } catch (err) {
    messageEl.textContent = err.message;
  }
}

async function playMove(from, to) {
  busy = true;
  try {
    const data = await api("/api/move", {
      method: "POST",
      body: JSON.stringify({ state, from, to }),
    });
    state = data.state;
    selected = null;
    hints = [];
    render();
    if (modeEl.value === "ai" && state.winner === null && state.turn === 1) {
      messageEl.textContent = "The consul considers the ranks…";
      await new Promise((resolve) => setTimeout(resolve, 420));
      const ai = await api("/api/ai-move", {
        method: "POST",
        body: JSON.stringify({ state }),
      });
      state = ai.state;
      render();
    }
    if (state.winner === null) {
      messageEl.textContent = state.unlocked
        ? "The back ranks are open."
        : "Advance the front lines onto rows 3 and 4 to unseal the rear.";
    }
  } catch (err) {
    messageEl.textContent = err.message;
  } finally {
    busy = false;
  }
}

async function newGame() {
  const data = await api("/api/new");
  state = data.state;
  selected = null;
  hints = [];
  messageEl.textContent = "Select a gold piece to begin.";
  render();
}

document.getElementById("new-game").addEventListener("click", newGame);
modeEl.addEventListener("change", newGame);

newGame().catch((err) => {
  messageEl.textContent = err.message;
});
