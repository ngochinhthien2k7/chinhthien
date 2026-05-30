import json
import os
from settings import *

LEADERBOARD_FILE = "leaderboard.json"
MAX_SCORES = 5


def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []


def save_leaderboard(scores):
    try:
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(scores, f, indent=2)
    except:
        pass


def add_score(score, name="Player"):
    scores = load_leaderboard()
    scores.append({"name": name, "score": score})
    scores.sort(key=lambda x: x["score"], reverse=True)
    scores = scores[:MAX_SCORES]
    save_leaderboard(scores)
    return scores


def get_leaderboard():
    return load_leaderboard()


def is_high_score(score):
    scores = get_leaderboard()
    if len(scores) < MAX_SCORES:
        return True
    return score > scores[-1]["score"]