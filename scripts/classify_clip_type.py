# scripts/classify_clip_type.py

import os
import requests
from get_top_clips import get_twitch_access_token

# Endpoints Twitch
HELIX_GAMES_URL = "https://api.twitch.tv/helix/games"
HELIX_CLIPS_URL = "https://api.twitch.tv/helix/clips"
CLIENT_ID       = os.getenv("TWITCH_CLIENT_ID")

def fetch_game_name_from_id(game_id, token):
    """
    Récupère le nom du jeu via son game_id avec l'API Helix /games.
    """
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    resp = requests.get(HELIX_GAMES_URL, headers=headers, params={"id": game_id})
    resp.raise_for_status()
    data = resp.json().get("data", [])
    if data:
        return data[0].get("name")
    return None

def fetch_game_id_from_clip_id(clip_id, token):
    """
    Si clip_data['game_id'] est absent, on va chercher le clip complet.
    """
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    resp = requests.get(HELIX_CLIPS_URL, headers=headers, params={"id": clip_id})
    resp.raise_for_status()
    data = resp.json().get("data", [])
    if data:
        return data[0].get("game_id")
    return None

def classify_clip_type(clip_data):
    """
    Renvoie 'chatting' si Just Chatting, 'gameplay' sinon.
    """
    token   = get_twitch_access_token()
    game_id = clip_data.get("game_id")

    # 1) Si pas de game_id, on essaye de récupérer via l'API
    if not game_id:
        game_id = fetch_game_id_from_clip_id(clip_data["id"], token)

    # 2) Si on a un game_id, on récupère le nom
    game_name = None
    if game_id:
        game_name = fetch_game_name_from_id(game_id, token)

    # 3) Classification par défaut
    if game_name:
        name_lower = game_name.lower()
        if "just chatting" in name_lower:
            return "chatting"
        else:
            return "gameplay"
    else:
        # Si pas de jeu associé => on considère que c'est du chat
        return "chatting"
