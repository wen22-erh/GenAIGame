import requests
import json

url = "http://localhost:11434/api/generate"

# 請確認這裡的模型名稱跟你電腦裡有的一樣
model_name = "llama3.1" 

data = {
    "model": model_name,
    "prompt": "你好，請回傳一句話證明你活著。",
    "stream": False
}

print(f"正在呼叫 {model_name}...")

try:
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print("成功！AI 回應：", response.json()['response'])
    else:
        print("失敗，狀態碼：", response.status_code)
        print("錯誤訊息：", response.text)
except Exception as e:
    print("連線錯誤：", e)
    print("請檢查 Ollama 是否有開啟 (http://localhost:11434)")