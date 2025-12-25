import requests
import json
import threading
from settings import * 
def get_battle_review(memmory_list, player_won):
    url = "http://localhost:11434/api/generate"
    if not memmory_list:
        memory_text="戰鬥瞬間結束 (無紀錄)"
    else:
        memory_text="\n".join(memmory_list)
    if player_won:
        outcome="戰鬥結束：你(火龍) 被 玩家 擊敗了！"
        attitude_instruction = """
        現在的狀況：你輸了！徹底輸了！
        你的心情：你極度不甘心，覺得這是不可能的，但事實擺在眼前。
        你的任務：用繁體中文寫一句「敗者的遺言」。你可以找藉口(例如: 我大意了)，誇獎玩家做得好的地方，但必須承認自己輸了。
        禁止事項：絕對不能說自己贏了。"""
    else:
        outcome="戰鬥結束：你(火龍) 殺死了 玩家！"
        attitude_instruction = """
        你贏了！看著倒下的人類，盡情展現你的傲慢與嘲諷吧。告訴他挑戰龍族是多麼愚蠢的行為。
        你的心情：你極度自豪，覺得自己無敵且高高在上。
        你的任務：用繁體中文寫一句「贏家的嘲諷」。你可以找藉口，盡情嘲諷玩家是多麼渺小。
        禁止事項：絕對不能說自己輸了。
        """
    prompt = f"""
    你是在遊戲裡的憤怒火龍boss。
    戰鬥已經結束 結果是{outcome}。
    你的戰鬥行動紀錄(以下是你在戰鬥中做過的事，不是玩家做的):{memory_text}
    你的發言指導:{attitude_instruction}
    請根據紀錄，用*繁體中文*評論對手。(30字以內)
    如果是你贏了，嘲笑他（例如提到他某次攻擊沒中）。
    如果是你輸了，不甘心地稱讚他。
    
    直接給出評論句子即可，不要 JSON。
    """
    data = {
        "model": MODEL,
        "prompt": prompt,   
        "stream": False
    }
    try:
        response = requests.post(url, json=data)
        result = response.json()['response']
        return result.strip()
    except :
        return "這戰鬥不值一提"
def ask_ollama(enemy_hp, player_hp, distance,attack_count,memory_list):
    url = "http://localhost:11434/api/generate"
    allow_heal = enemy_hp < 1500 
    
    heal_desc = '- "HEAL": 恢復血量。當你的血量低下時一定要馬上使用。\n' if allow_heal else ''
    if not memory_list:
        memory_text="無"
    else:
        memory_text="\n".join(memory_list)    
    if attack_count<2:
        skills_description = f"""
    可用招式清單 (請從中選擇技能):
    - "ULTIMATE": 終極毀滅你的最強絕招，在你血量低時一定要施放。威力巨大但消耗極大體力。接近死亡時一定要使用。
    - "TRACKING FIRE BALL": 追蹤火球。第二耗費體力的招式，帶有強烈殺意。當你憤怒或想確保命中時使用。
    - "FIRE BALL": 普通火球。剛開始用來試探對手的招式，所使用的攻擊手段。
    - "ATTACK": 近身肉搏。只有當(玩家)靠得太近。
    - "IDLE": (別用)待機。當你覺得游刃有餘，或者想觀察對手時使用，若是你一陣子沒扣血也可以使用，請盡量不使用此技能。
    {heal_desc}
    """
    else:
        skills_description = f"""
    可用招式清單 (請從中選擇技能):
    - "TRACKING FIRE BALL": 追蹤火球。
    - "FIRE BALL": 普通火球。
    - "ATTACK": 近身肉搏。只有當(玩家)靠得太近。
    - "IDLE": 待機。當你覺得游刃有餘，或者想觀察對手時使用，若是你一陣子沒受到玩家攻擊也可以使用。
    {heal_desc}
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
    你是在遊戲裡的憤怒火龍boss，可以說一些有關於火焰的台詞，或是有關於火龍對戰時會說的話。
    角色人設:(
    你原先高傲自大，看不起人類。你認為自己是高等生物。
    你有補血手段，在血量第一次低於50%要直接使用補血手段。
    但當你的血量過低時(低於20%)，你處於瀕死邊緣！你的傲慢已經崩塌。你會不顧一切反擊。
    你的對話必須簡短有力用，只使用繁體中文(10字以內)，並符合上述人設。)

    
    目前戰況:
    - 我的血量: {enemy_hp}
    - 我的血量狀態: {danger_level}
    - 玩家血量: {player_hp}
    - 與玩家的距離: {int(distance)}
    
    短期戰鬥記憶 (過去 3 回合):
    {memory_text}
    可用招式清單:
    {skills_description}
    你的任務:(
    請觀察目前的戰況和我的血量狀態，結合你的角色人設，判斷現在最適合的戰術，並選擇一個技能。)

    請只回傳 JSON 格式，不要有其他廢話：
    {{
        "strategy": "從可用招式清單中選一個",
        "should_attack": true 或 false,
        "message": "你只能用繁體中文台詞(10字內，展現你的個性)"
    }}
    """
    data = {
        "model": MODEL,
        "prompt": prompt,
        "format": "json",  
        "stream": False
    }
    try:
        response = requests.post(url, json=data)
        result = json.loads(response.json()['response'])
        return result
    except Exception as e:
        print(f"LLM Error: {e}")
        return {"strategy": "IDLE", "should_attack": False, "message": "..."} 