import requests
import json
import threading

def ask_ollama(enemy_hp, player_hp, distance,attack_count):
    url = "http://localhost:11434/api/generate"
    if attack_count<2:
        skills_description = """
    可用招式清單 (請從中選擇技能):
    - "ULTIMATE": 終極毀滅你的最強絕招，請謹慎使用，只能使兩次。威力巨大但消耗極大體力。是你被逼入絕境、接近死亡時才會使用。
    - "TRACKING FIRE BALL": 追蹤火球。帶有強烈殺意的招式。當你憤怒或想確保命中時使用。
    - "FIRE BALL": 普通火球。用來打發時間或試探對手。
    - "ATTACK": 近身肉搏。只有當那隻卑微的蟲子(玩家)靠得太近。
    - "IDLE": 待機。當你覺得游刃有餘，或者想觀察對手時使用，若是你一陣子沒受到玩家攻擊也可以使用。
    """
    else:
        skills_description = """
    可用招式清單 (請從中選擇技能):
    - "TRACKING FIRE BALL": 追蹤火球。帶有強烈殺意的招式。當你憤怒或想確保命中時使用。
    - "FIRE BALL": 普通火球。用來打發時間或試探對手。
    - "ATTACK": 近身肉搏。只有當那隻卑微的蟲子(玩家)靠得太近。
    - "IDLE": 待機。當你覺得游刃有餘，或者想觀察對手時使用，若是你一陣子沒受到玩家攻擊也可以使用。
    """
    danger_level="安全"
    if enemy_hp < 200:
        danger_level= "危急"
    elif enemy_hp < 700:
        danger_level = "中等"
    elif enemy_hp < 1500:
        danger_level = "良好"
    elif enemy_hp < 2000:
        danger_level = "安全"

    prompt = f"""
    你是在扮演遊戲裡的小火龍boss。
    角色人設:(
    你原先極度自大，看不起人類。你認為自己是高等生物。
    但當你的血量過低時(低於10%)，你現在處於瀕死邊緣！你的傲慢已經崩塌。你會不顧一切反擊。
    你的對話必須簡短有力 (10字以內)，並符合上述人設。)

    
    目前戰況:
    - 我的血量: {enemy_hp}
    - 我的血量狀態: {danger_level}
    - 玩家血量: {player_hp}
    - 與玩家的距離: {int(distance)}
    {skills_description}
    你的任務:(
    請觀察目前的戰況和我的血量狀況，結合你的角色人設，判斷現在最適合的戰術，並選擇一個技能。
    (例如:你現在血量不多，或玩家離你太遠，你可以選擇使用追蹤火球))

    請只回傳 JSON 格式，不要有其他廢話：
    {{
        "strategy": "從可用招式清單中選一個",
        "should_attack": true 或 false,
        "message": "根據戰況與人設說的一句話"
    }}
    """
    data = {
        "model": "llama3.1",  # 或是你電腦跑得動的模型，如 mistral, qwen2.5:7b
        "prompt": prompt,
        "format": "json",   # 強制 Ollama 輸出 JSON
        "stream": False
    }
    try:
        response = requests.post(url, json=data)
        result = json.loads(response.json()['response'])
        return result
    except Exception as e:
        print(f"LLM Error: {e}")
        return {"strategy": "IDLE", "should_attack": False, "message": "..."} # 發生錯誤時的預設值