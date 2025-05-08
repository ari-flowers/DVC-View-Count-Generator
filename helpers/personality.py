PERSONALITY_VIEW_TARGETS = {
    "Silent": 0,
    "Solitary": 1,
    "Reserved": 5,
    "Mischievous": 50,
    "Lousy": 95,
    "Friendly": 100,
    "Extroverted": 100,
    "Cute": 199,
    "Lovely": 300,
    "Arrogant": 200,
}

def apply_lovely_bonus(default_target=300):
    has_bonus = input("💬 Are you using Sea Creature Calling or a View Count Amulet? (y/n): ").strip().lower()
    if has_bonus == 'y':
        print("🐠 Adjusted target to 200 views based on in-game bonus.")
        return 200
    else:
        print("⚠️ Max achievable views may fall short of 300. You’ll need to supplement the rest. Good luck, tamer!")
        return default_target

def match_personality_input(user_input, personality_dict):
    user_input = user_input.lower()
    matches = [
        key for key in personality_dict
        if key.lower().startswith(user_input)
    ]
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        print("⚠️ Ambiguous input. Did you mean one of:")
        for m in matches:
            print(f" - {m}")
        return None
    else:
        print("❌ No matching personality found. Available options:")
        for key in personality_dict:
            print(f" - {key}")
        return None

def resolve_personality_goal(user_input):
    """Returns (personality_name, target_views) or (None, None) on failure."""
    matched = match_personality_input(user_input, PERSONALITY_VIEW_TARGETS)
    if not matched:
        return None, None
    if matched == "Lovely":
        target_views = apply_lovely_bonus()
    else:
        target_views = PERSONALITY_VIEW_TARGETS[matched]
    return matched, target_views