import requests
import json
import threading

def ask_ollama(enemy_hp, player_hp, distance):
    url = "http://localhost:11434/api/generate"
    prompt = f"""
    你是一個遊戲裡的小火龍boss。
    目前狀態：
    - 我的血量: {enemy_hp}
    - 玩家血量: {player_hp}
    - 與玩家的距離: {int(distance)}
    
    請根據以下優先級制定戰術（從高到低）：
    
    1. 如果我的血量低於 30，請選擇 "ULTIMATE" (開大招)，should_attack 設為 false
    2. 如果我的血量低於 200，請一直選擇 "DOUBLE FIRE BALL" (追蹤火焰球)，should_attack 設為 true
    3. 如果與玩家的距離大於 400，請選擇 "FIRE BALL" (火焰球)，should_attack 設為 true
    4. 如果與玩家的距離小於 200，請選擇 "ATTACK" (近身攻擊)，should_attack 設為 false
    5. 其他情況選擇 "IDLE" (待機)，should_attack 設為 false
    
    請只回傳 JSON 格式，不要有其他廢話：
    {{
        "strategy": "策略名稱",
        "should_attack": true 或 false,
        "message": "簡短的嗆聲或台詞"
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