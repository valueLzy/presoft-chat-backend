import requests
from openai import OpenAI
from zhipuai import ZhipuAI
apikey = "e479f5521d65e3c5d358341a6e2f6c0e.Ci18igbfpxoyuhHp"

#流式返回用这个######################################
def glm4_9b_chat_ws(history,temperature):
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


#http请求走这个######################################
url = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
def glm4_9b_chat_http(messages,temperature):
    # 定义请求体
    headers = {
        "Authorization": f"Bearer e479f5521d65e3c5d358341a6e2f6c0e.Ci18igbfpxoyuhHp"
    }
    data = {
        "model": "glm-4-0520",  # 替换为你使用的模型名
        "messages": messages,
        "temperature": temperature,
        "do_sample": True,
    }

    # 发起POST请求
    response = requests.post(url, json=data, headers=headers)
    # 处理响应
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        return f"请求失败，状态码：{response.status_code}"


def deepseek_chat(temperature, messages):
    client = OpenAI(api_key="sk-10132368a7724831833d6b8ccf28ad42", base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=True,
        temperature=temperature,
    )
    return response