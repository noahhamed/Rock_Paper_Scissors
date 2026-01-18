# RPS.py
import random

RPS = ("R", "P", "S")
BEATS = {"R": "S", "P": "R", "S": "P"}     # key beats value
COUNTER = {"R": "P", "P": "S", "S": "R"}   # key is beaten by value

QUINCY_PATTERN = ["R", "R", "P", "P", "S"]


def _most_common(moves):
    if not moves:
        return "R"
    c = {"R": 0, "P": 0, "S": 0}
    for m in moves:
        if m in c:
            c[m] += 1
    # stable tie-break
    return max(("R", "P", "S"), key=lambda x: (c[x], -("RPS".index(x))))


def _quincy_offset(opp_hist):
    # find best alignment of opponent history to Quincy pattern
    best_off = 0
    best_score = -1
    n = len(opp_hist)
    for off in range(5):
        score = 0
        for i in range(n):
            if opp_hist[i] == QUINCY_PATTERN[(off + i) % 5]:
                score += 1
        if score > best_score:
            best_score = score
            best_off = off
    return best_off, (best_score / n if n else 0.0)


def _looks_like_quincy(opp_hist):
    if len(opp_hist) < 10:
        return False
    _, ratio = _quincy_offset(opp_hist)
    return ratio >= 0.9


def _looks_like_kris(opp_hist, my_hist):
    # kris plays COUNTER(my_previous)
    n = min(len(opp_hist), len(my_hist) - 1)
    if n < 6:
        return False
    start = max(0, len(opp_hist) - 25)
    good = 0
    checked = 0
    for t in range(start, len(opp_hist)):
        if t - 1 < 0 or t - 1 >= len(my_hist):
            continue
        checked += 1
        if opp_hist[t] == COUNTER.get(my_hist[t - 1], None):
            good += 1
    return checked >= 6 and good / checked >= 0.7


def _looks_like_mrugesh(opp_hist, my_hist):
    # mrugesh plays COUNTER(most_common(my last 10))
    if len(opp_hist) < 12 or len(my_hist) < 11:
        return False
    start = max(1, len(opp_hist) - 30)
    good = 0
    checked = 0
    for t in range(start, len(opp_hist)):
        window = my_hist[max(0, t - 10):t]
        if not window:
            continue
        expected_opp = COUNTER[_most_common(window)]
        checked += 1
        if opp_hist[t] == expected_opp:
            good += 1
    return checked >= 8 and good / checked >= 0.6


def player(prev_play, state={"opp": [], "me": [], "trans": None, "rng": None}):
    # New match reset
    if prev_play == "":
        state["opp"] = []
        state["me"] = []
        state["trans"] = {a + b: 0 for a in RPS for b in RPS}  # bigram counts of OUR moves
        state["rng"] = random.Random(1337)

    rng = state["rng"]
    opp_hist = state["opp"]
    my_hist = state["me"]
    trans = state["trans"]

    if prev_play in RPS:
        opp_hist.append(prev_play)

    # --- Detect which bot it is ---
    is_quincy = _looks_like_quincy(opp_hist)
    is_kris = _looks_like_kris(opp_hist, my_hist)
    is_mrugesh = _looks_like_mrugesh(opp_hist, my_hist)

    # --- Choose move ---
    if is_quincy:
        off, _ = _quincy_offset(opp_hist)
        predicted = QUINCY_PATTERN[(off + len(opp_hist)) % 5]
        move = COUNTER[predicted]

    elif is_kris:
        # kris plays COUNTER(my_last), so play BEATS[my_last]
        last_my = my_hist[-1] if my_hist else "R"
        move = BEATS[last_my]

    elif is_mrugesh:
        # mrugesh plays COUNTER(most_common(my last 10)), so play BEATS[most_common]
        m = _most_common(my_hist[-10:])
        move = BEATS[m]

    else:
        # abbey predicts our next move based on bigram counts from our last move,
        # then plays COUNTER(prediction). So we play BEATS[prediction].
        last_my = my_hist[-1] if my_hist else "R"
        candidates = [last_my + "R", last_my + "P", last_my + "S"]
        pred_pair = max(candidates, key=lambda k: trans.get(k, 0))
        predicted = pred_pair[-1]

        move = BEATS[predicted]

        # tiny randomness so Abbey can’t lock in perfectly
        if rng.random() < 0.05:
            move = rng.choice(RPS)

    # update OUR transition counts
    if my_hist:
        trans[my_hist[-1] + move] += 1

    my_hist.append(move)
    return move
