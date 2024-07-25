
import json
from typing import List

import uvicorn
from fastapi import FastAPI, WebSocket
from starlette.responses import JSONResponse
from pydantic import BaseModel

from api.article_writing import get_outline
from llm.glm4 import glm4_9b_chat
from util.websocket_utils import ConnectionManager


# 普通对话接口#####

def init_flask():
    app = FastAPI()
    class Question(BaseModel):
        prompt: str
        history: List[dict[str, str]]
        temperature: int

    class User(BaseModel):
        username: str
        password: str

    class Title(BaseModel):
        article_title: str

    # 登录##############################################################
    @app.post("/login")
    def login(user: User):
        with open('user.json', 'r', encoding='utf-8') as file:
            users = json.load(file)
        # 遍历用户列表，查找匹配的用户名和密码
        for stored_user in users:
            if stored_user['username'] == user.username and stored_user['password'] == user.password:
                return JSONResponse(content=stored_user)
            else:
                return("用户名或密码不正确")

    # 普通对话##############################################################
    @app.websocket("/commonchat/{v1}")
    async def commonchat(websocket: WebSocket, v1: str):
        manager = ConnectionManager()
        await manager.connect(websocket)
        try:
            data = await websocket.receive_text()
            params = Question.parse_raw(data)
            prompt = params.prompt
            history = params.history
            history.append({"content": prompt, "role": "user"})
            temperature = params.temperature

            answer = glm4_9b_chat(history, temperature)
            for chunk in answer:
                await manager.send_personal_message(json.dumps({
                    "answer": chunk.choices[0].delta.content
                }, ensure_ascii=False), websocket)

        except Exception as e:
            print(e)

    # 生成大纲##############################################################
    @app.post("/getarticle")
    def getarticle(title: Title):
        getarticle = get_outline(title.article_title, 0.7)
        print(getarticle)



    return app


app = init_flask()
uvicorn.run(app, host='0.0.0.0', port=8001, workers=1, timeout_keep_alive=300)
