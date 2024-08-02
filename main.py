import asyncio
import json
import uuid

import uvicorn
from fastapi import FastAPI, WebSocket, UploadFile, File, Form
from starlette.responses import JSONResponse

from api.article_writing import get_outline, get_summary, get_keywords, extract_content_from_json, get_body, \
    list_to_query, revise_article
from db.sql import get_user_with_menus, check_username_exists, insert_user

from llm.glm4 import glm4_9b_chat_ws
from util.websocket_utils import ConnectionManager
from utils import get_hashed_password
from models.entity import Question, UserLogin, UserRegister, Basic, Article, Edit

# 普通对话接口#####

def init_flask():
    app = FastAPI()

    # 登录##############################################################
    @app.post("/login")
    def login(user: UserLogin):
        # 获取用户及其菜单信息
        user_info = get_user_with_menus(user.username, get_hashed_password(user.password), user.language)

        if not user_info:
            return JSONResponse(status_code=404, content={"message": "用户名或密码不存在"})

        # 假设返回的用户信息是列表形式，并且列表中只有一个元素
        user_data = user_info[0]

        # 将菜单名称从字符串转换为列表
        menu_names = user_data[3].split(',')

        # 构建返回的数据结构
        return JSONResponse(content={
            "userId": user_data[0],
            "userName": user_data[1],
            "roles": user_data[2],
            "menuName": menu_names,
            "desc": user_data[4],
            "password": user_data[5]
        })

    @app.post("/register")
    def register(user: UserRegister):
        # 获取用户及密码
        user_name = user.username
        user_password = get_hashed_password(user.password)
        # 判断用户名是否存在
        if check_username_exists(user_name):
            return JSONResponse(status_code=501, content={"message": "用户名存在"})
        else:
            insert_user(str(uuid.uuid4()), user_name, '用户', '1,2,3,4,5', '', user_password, user.company, user.nationality)
            return JSONResponse(status_code=200, content={"message": "success"})

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

            answer = glm4_9b_chat_ws(history, temperature)
            for chunk in answer:
                await manager.send_personal_message(json.dumps({
                    "answer": chunk.choices[0].delta.content
                }, ensure_ascii=False), websocket)

        except Exception as e:
            print(e)

    # 论文---获取关键词##############################################################
    @app.get("/getkeywords")
    def getkeywords():
        keywords = ["gis", "作战仿真系统", "卫星定位", "弹道控制", "数据库",
                    "数据融合", "最优布站", "毁伤评估", "特情处理", "目标跟踪", "红蓝对抗",
                    "网络对抗", "联合弹药毁伤", "视觉仿真", "训练考核评价"]
        return {"keywordlist": keywords}

    # 论文---生成大纲##############################################################
    @app.post("/getbasic")
    def getbasic(basic: Basic):
        return get_outline(basic.article_title, 0.7, basic.article_base)

    # 论文---生成论文##############################################################
    @app.websocket("/getarticle/{v1}")
    async def commonchat(websocket: WebSocket, v1: str):
        manager = ConnectionManager()
        await manager.connect(websocket)
        try:
            data = await websocket.receive_text()
            params = Article.parse_raw(data)
            article_base = params.article_base
            article_choices = params.article_choices
            ref_file = []
            #摘要
            summary = get_summary(article_base,list_to_query(article_choices))
            for chunk in summary["ai_say"]:
                await manager.send_personal_message(json.dumps({
                    "summary": chunk.choices[0].delta.content
                }, ensure_ascii=False), websocket)
            #关键字
            keywords = get_keywords(article_base)
            await manager.send_personal_message(json.dumps({
                "keywords": keywords
            }, ensure_ascii=False), websocket)
            # 正文
            json_list = extract_content_from_json(article_base)
            for index, item in enumerate(json_list):
                print(index,item)
                if '标题' in item and index != len(json_list) - 1:
                    await manager.send_personal_message(json.dumps({
                        "biaoti": item['标题']
                    }, ensure_ascii=False), websocket)
                elif '小节标题' in item:
                    await manager.send_personal_message(json.dumps({
                        "xiaojiebiaoti": item['小节标题']
                    }, ensure_ascii=False), websocket)
                    body = get_body(article_base, str(item), list_to_query(article_choices))
                    if body['ref_file']:
                        for x in body['ref_file']:
                            ref_file.append(x)
                    for chunk in body['ai_say']:
                        await manager.send_personal_message(json.dumps({
                            "xiaojieneirong": chunk.choices[0].delta.content
                        }, ensure_ascii=False), websocket)
                elif '标题' in item and index == len(json_list) - 1:
                    await manager.send_personal_message(json.dumps({
                        "xiaojiebiaoti": item['标题']
                    }, ensure_ascii=False), websocket)
                    body = get_body(article_base ,str(item), list_to_query(article_choices))
                    for chunk in body['ai_say']:
                        await manager.send_personal_message(json.dumps({
                            "xiaojieneirong": chunk.choices[0].delta.content
                        }, ensure_ascii=False), websocket)
                    if body['ref_file']:
                        for x in body['ref_file']:
                            ref_file.append(x)
            # 引用
            await manager.send_personal_message(json.dumps({
                "yinyong": ref_file
            }, ensure_ascii=False), websocket)

        except Exception as e:
            print(e)

    # 论文---修改章节##############################################################
    @app.websocket("/editarticle/{v1}")
    async def editarticle(websocket: WebSocket, v1: str):
        manager = ConnectionManager()
        await manager.connect(websocket)
        try:
            data = await websocket.receive_text()
            params = Edit.parse_raw(data)
            oldpart = params.oldpart
            prompt = params.prompt
            # content = get_value_if_key_in_dicts(article_base, chapter)
            # if content == '':
            #     return JSONResponse(status_code=404, content={"message": "您输入的标题不存在，请检查后重新输入"})
            # else:
            revise_text = revise_article(oldpart, prompt)
            for chunk in revise_text:
                await manager.send_personal_message(json.dumps({
                    "newpart": chunk.choices[0].delta.content
                }, ensure_ascii=False), websocket)

        except Exception as e:
            print(e)

    # 日语修正##############################################################
    @app.post("/correctJa")
    async def correctJa(file: UploadFile = File(None), prompt: str = Form(None)):
        if file:
            return JSONResponse(content={"message": "收到文件"})
        elif prompt:
            return JSONResponse(content={"message": "收到"})
        else:
            return JSONResponse(content={"message": "没有收到文件或prompt"})








    return app


app = init_flask()
uvicorn.run(app, host='0.0.0.0', port=8001, workers=1, timeout_keep_alive=300)
