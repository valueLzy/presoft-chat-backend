from llm.glm4 import glm4_9b_chat_ws


def ordinary(temperature, prompt, history):
    history.append({"content": prompt,
                    "role": "user"
                    })
    history.insert(0, {"role": "system", "content": "あなたはPreSoftが開発しているaiアシスタントで、あなたの名前はYiです。人々の様々な問題を解決することを目的としています。"})
    return glm4_9b_chat_ws(temperature, history)
