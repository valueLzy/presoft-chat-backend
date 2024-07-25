from zhipuai import ZhipuAI
apikey = "e479f5521d65e3c5d358341a6e2f6c0e.Ci18igbfpxoyuhHp"

def glm4_9b_chat(history,temperature):
    client = ZhipuAI(api_key=apikey)
    history.insert(0, {"role": "system",
                       "content": "你是PreSoft开发的人工智能助手，你的名字是Yi，请解决人们的各种问题。"})
    response = client.chat.completions.create(
        model="glm-4",
        messages=history,
        temperature=temperature,
        stream=True,
    )
    return response
