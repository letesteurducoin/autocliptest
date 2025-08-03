def classify_clip_type(clip_data):
    game_name = (clip_data.get('game_name') or '').lower()
    chatting_keywords = ['just chatting', 'justchatting', 'discussion', 'talk']
    if any(k in game_name for k in chatting_keywords):
        return 'chatting'
    return 'gameplay'