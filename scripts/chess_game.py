"""Community chess played through GitHub Issues.

    python scripts/chess_game.py move     # handle one issue (env: ISSUE_TITLE, ISSUE_AUTHOR)
    python scripts/chess_game.py render   # rebuild chess/board.svg and the README section from state

Issue titles:  chess|move|e2e4   (promotion: chess|move|e7e8q)
               chess|new         (only once the current game is over)

State lives in chess/state.json; the whole game is replayed from its move list each run,
so the file is the single source of truth. The reply for the issue is written to
$COMMENT_FILE and `changed=true|false` to $GITHUB_OUTPUT.
"""
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

import chess
import chess.svg

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "chess" / "state.json"
BOARD_SVG = ROOT / "chess" / "board.svg"
README = ROOT / "README.md"
START, END = "<!--START_SECTION:chess-->", "<!--END_SECTION:chess-->"

REPO = os.environ.get("GITHUB_REPOSITORY", "Manas-Maahir/Manas-Maahir")
PROFILE = f"https://github.com/{REPO.split('/')[0]}"
UCI = re.compile(r"^[a-h][1-8][a-h][1-8][qrbn]?$")

BOARD_COLORS = {
    "square light": "#e3e6f0",
    "square dark": "#7f8fb8",
    "square light lastmove": "#f3dfa2",
    "square dark lastmove": "#d4b86a",
    "margin": "#1f2335",
    "coord": "#c0caf5",
}


def new_state(game=1, leaderboard=None, past=None):
    return {"game": game, "moves": [], "leaderboard": leaderboard or {}, "past_games": past or []}


def load():
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else new_state()


def save(state):
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def replay(state):
    board = chess.Board()
    for m in state["moves"]:
        board.push_uci(m["uci"])
    return board


def issue_link(title):
    body = "Just press **Create** — the title is your move. No need to write anything."
    return f"https://github.com/{REPO}/issues/new?title={quote(title)}&body={quote(body)}"


def describe_end(board):
    outcome = board.outcome(claim_draw=True)
    reason = outcome.termination.name.replace("_", " ").lower()
    winner = {True: "White wins", False: "Black wins", None: "Draw"}[outcome.winner]
    return outcome.result(), f"{winner} by {reason}"


def render(state):
    board = replay(state)
    last = board.peek() if board.move_stack else None
    check = board.king(board.turn) if board.is_check() else None
    BOARD_SVG.write_text(
        chess.svg.board(board, lastmove=last, check=check, size=440,
                        orientation=board.turn, colors=BOARD_COLORS),
        encoding="utf-8",
    )

    n = len(state["moves"])
    lines = [
        '<div align="center">',
        "",
        f'<img src="chess/board.svg?v={state["game"]}-{n}" width="440" alt="Current position of the community chess game">',
        "",
    ]

    if board.is_game_over(claim_draw=True):
        result, text = describe_end(board)
        lines += [f"**Game #{state['game']} is over: {text} ({result}).**", "",
                  f"[**♟ Start a new game**]({issue_link('chess|new')})", "", "</div>"]
    else:
        side = "⚪ White" if board.turn == chess.WHITE else "⚫ Black"
        status = " — **check!**" if board.is_check() else ""
        lines += [f"**Game #{state['game']} · move {board.fullmove_number} · {side} to play**{status}", "",
                  "Anyone can play: pick a move below. It opens a pre-filled issue — press <b>Create</b> and the board updates in about a minute.",
                  "", "</div>", "",
                  "<details>",
                  f"<summary><b>Choose {side.split()[1]}'s move</b></summary>",
                  "", "| From | To |", "| :---: | --- |"]
        by_from = defaultdict(list)
        for mv in board.legal_moves:
            by_from[mv.from_square].append(mv)
        for sq in sorted(by_from, key=lambda s: (chess.square_file(s), chess.square_rank(s))):
            piece = board.piece_at(sq).unicode_symbol()
            links = " · ".join(
                f"[{chess.square_name(m.to_square).upper()}"
                f"{'=' + chess.piece_symbol(m.promotion).upper() if m.promotion else ''}]"
                f"({issue_link('chess|move|' + m.uci())})"
                for m in sorted(by_from[sq], key=lambda m: (m.to_square, m.promotion or 0))
            )
            lines.append(f"| {piece} **{chess.square_name(sq).upper()}** | {links} |")
        lines += ["", "</details>"]

    if state["moves"]:
        lines += ["", "<details>", "<summary><b>Last moves</b></summary>", "",
                  "| # | Move | Player |", "| :---: | :---: | --- |"]
        for i in range(n - 1, max(n - 6, 0) - 1, -1):
            m = state["moves"][i]
            num = f"{i // 2 + 1}." + ("" if i % 2 == 0 else "..")
            lines.append(f"| {num} | {m['san']} | [@{m['by']}](https://github.com/{m['by']}) |")
        lines += ["", "</details>"]

    if state["leaderboard"]:
        top = sorted(state["leaderboard"].items(), key=lambda kv: (-kv[1], kv[0].lower()))[:5]
        players = " · ".join(f"[@{u}](https://github.com/{u}) ({c})" for u, c in top)
        lines += ["", f"**Most moves played:** {players}"]
    if state["past_games"]:
        recent = " · ".join(f"#{g['game']}: {g['summary']} in {g['moves']} moves" for g in state["past_games"][-3:][::-1])
        lines += ["", f"<sub>Previous games — {recent}</sub>"]

    text = README.read_text(encoding="utf-8")
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    README.write_text(head + START + "\n" + "\n".join(lines) + "\n" + END + tail, encoding="utf-8")


def handle(title, author):
    """Returns (changed, reply)."""
    state = load()
    board = replay(state)
    parts = [p.strip().lower() for p in title.split("|")]
    back = f"\n\n[Back to the board]({PROFILE})"

    if parts[:2] == ["chess", "new"]:
        if not board.is_game_over(claim_draw=True):
            return False, f"Game #{state['game']} is still in progress — jump in with a move instead!{back}"
        result, text = describe_end(board)
        past = state["past_games"] + [{"game": state["game"], "result": result, "summary": text,
                                       "moves": len(state["moves"])}]
        save(new_state(state["game"] + 1, state["leaderboard"], past))
        render(load())
        return True, f"Game #{state['game'] + 1} has started — ⚪ White to play. Make the first move!{back}"

    if len(parts) != 3 or parts[:2] != ["chess", "move"] or not UCI.match(parts[2]):
        return False, "I couldn't read that move. Use the links on the profile page — they fill the title in for you." + back

    if board.is_game_over(claim_draw=True):
        return False, f"Game #{state['game']} is already over. [Start a new one]({issue_link('chess|new')})!{back}"

    if state["moves"] and state["moves"][-1]["by"].lower() == author.lower():
        return False, f"You made the last move, @{author} — let someone else answer first, then come back.{back}"

    move = chess.Move.from_uci(parts[2])
    if move not in board.legal_moves:
        return False, (f"`{parts[2]}` isn't legal in the current position — someone may have moved first. "
                       f"Pick again from the updated list.{back}")

    san = board.san(move)
    board.push(move)
    state["moves"].append({"uci": move.uci(), "san": san, "by": author})
    state["leaderboard"][author] = state["leaderboard"].get(author, 0) + 1
    save(state)
    render(state)

    reply = f"Played **{san}** — thanks @{author}! ♟"
    if board.is_game_over(claim_draw=True):
        result, text = describe_end(board)
        reply += f"\n\nThat ends game #{state['game']}: **{text} ({result})**."
    return True, reply + back


def main():
    if sys.argv[1:] == ["render"]:
        if not STATE.exists():
            save(new_state())
        render(load())
        return
    changed, reply = handle(os.environ["ISSUE_TITLE"], os.environ["ISSUE_AUTHOR"])
    Path(os.environ.get("COMMENT_FILE", "comment.md")).write_text(reply + "\n", encoding="utf-8")
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
            out.write(f"changed={'true' if changed else 'false'}\n")
    print(reply)


if __name__ == "__main__":
    main()
