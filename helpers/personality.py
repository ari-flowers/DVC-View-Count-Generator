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

def resolve_personality_goal(user_input, current_views=0):
    """Returns (personality_name, target_views, bonus_used) or (None, None, None) on failure."""
    matched = match_personality_input(user_input, PERSONALITY_VIEW_TARGETS)
    if not matched:
        return None, None, None

    base_target = PERSONALITY_VIEW_TARGETS[matched]
    remaining = base_target - current_views

    if base_target > 100 and remaining > 100:
        has_bonus = input(f"💬 Are you using Sea Creature Calling or a View Count Amulet for '{matched}'? (y/n): ").strip().lower()
        if has_bonus == 'y':
            new_target = base_target - 100
            print(f"🐠 Adjusted target to {new_target} views based on in-game bonus.")
            return matched, new_target, True
        else:
            print(f"⚠️ Max achievable views may fall short of {base_target}. You’ll need to supplement the rest. Good luck, tamer!")
            return matched, base_target, False
    else:
        return matched, base_target, False