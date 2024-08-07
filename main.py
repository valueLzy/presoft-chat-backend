import asyncio
import json
import os
import shutil
import uuid

import openpyxl
import uvicorn
from fastapi import FastAPI, WebSocket, UploadFile, File, Form
from openpyxl.utils import get_column_letter
from starlette.responses import JSONResponse

from api.article_writing import get_outline, get_summary, get_keywords, extract_content_from_json, get_body, \
    list_to_query, revise_article
from db.sql import get_user_with_menus, check_username_exists, insert_user
from knowledge.dataset_api import matching_paragraph
from llm.embeddings import bg3_m3, rerank

from llm.glm4 import glm4_9b_chat_ws
from milvus.milvus_tools import create_milvus, insert_milvus, delete_milvus, get_milvus_collections_info, del_entity
from prompt import file_chat_prompt
from prompts import del_japanese_prompt, del_japanese_prompt_ws
from util.websocket_utils import ConnectionManager
from utils import md5_encrypt, download_file, put_file, has_japanese, get_red_text_from_docx, \
    replace_text_in_docx, parse_file_other, parse_file_pdf
from models.entity import Question, UserLogin, UserRegister, Basic, Article, Edit, JachatCorrect, \
    JafileCorrect, Filechat1, Filechat2, ResponseEntity


def init_flask():
    app = FastAPI()

    # 登录##############################################################
    @app.post("/user/login")
    def login(user: UserLogin):
        # 获取用户及其菜单信息
        user_info = get_user_with_menus(user.username, md5_encrypt(user.password), user.language)

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

    # 注册##############################################################
    @app.post("/user/register")
    def register(user: UserRegister):
        # 获取用户及密码
        user_name = user.username
        user_password = md5_encrypt(user.password)
        # 判断用户名是否存在
        if check_username_exists(user_name):
            return JSONResponse(status_code=501, content={"message": "用户名存在"})
        else:
            insert_user(str(uuid.uuid4()), user_name, '用户', '1,2,3,4,5', '', user_password, user.company,
                        user.nationality)
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
        finally:
            manager.disconnect(websocket)

    # 论文---获取关键词##############################################################
    @app.get("/write/getkeywords")
    def getkeywords():
        keywords = ["gis", "作战仿真系统", "卫星定位", "弹道控制", "数据库",
                    "数据融合", "最优布站", "毁伤评估", "特情处理", "目标跟踪", "红蓝对抗",
                    "网络对抗", "联合弹药毁伤", "视觉仿真", "训练考核评价"]
        return {"keywordlist": keywords}

    # 论文---生成大纲##############################################################
    @app.post("/write/getbasic")
    def getbasic(basic: Basic):
        return get_outline(basic.article_title, 0.7, basic.article_base)

    # 论文---生成论文##############################################################
    @app.websocket("/write/getarticle/{v1}")
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
            summary = get_summary(article_base, list_to_query(article_choices))
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
                print(index, item)
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
                    body = get_body(article_base, str(item), list_to_query(article_choices))
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
        finally:
            manager.disconnect(websocket)

    # 论文---修改章节##############################################################
    @app.websocket("/write/editarticle/{v1}")
    async def editarticle(websocket: WebSocket, v1: str):
        manager = ConnectionManager()
        await manager.connect(websocket)
        try:
            data = await websocket.receive_text()
            params = Edit.parse_raw(data)
            oldpart = params.oldpart
            prompt = params.prompt
            revise_text = revise_article(oldpart, prompt)
            for chunk in revise_text:
                await manager.send_personal_message(json.dumps({
                    "newpart": chunk.choices[0].delta.content
                }, ensure_ascii=False), websocket)

        except Exception as e:
            print(e)
        finally:
            manager.disconnect(websocket)

    # 日语修正-对话##############################################################
    @app.websocket("/correctJa/chat/{v1}")
    async def correctJachat(websocket: WebSocket, v1: str):
        manager = ConnectionManager()
        await manager.connect(websocket)
        try:
            data = await websocket.receive_text()
            params = JachatCorrect.parse_raw(data)
            prompt = params.prompt
            answer = del_japanese_prompt_ws(prompt)
            for chunk in answer:
                await manager.send_personal_message(json.dumps({
                    "answer": chunk.choices[0].delta.content
                }, ensure_ascii=False), websocket)

        except Exception as e:
            print(e)
        finally:
            manager.disconnect(websocket)

    # 日语修正-文件##############################################################
    @app.websocket("/correctJa/file/{v1}")
    async def correctJafile(websocket: WebSocket, v1: str):
        manager = ConnectionManager()
        await manager.connect(websocket)
        try:
            data = await websocket.receive_text()
            params = JafileCorrect.parse_raw(data)
            bucket_name = params.bucket_name
            object_name = params.object_name
            download_file_res = download_file(bucket_name, object_name)
            file_path = download_file_res['file_path']
            file_dir = download_file_res['file_dir']
            file_type = object_name.split('.')[1]
            new_file_path = file_path.replace(object_name, 'new_' + object_name)
            if file_type == 'xlsx' or file_type == 'xls':
                # 加载工作簿和工作表
                workbook = openpyxl.load_workbook(file_path)
                for sheet in workbook.sheetnames:
                    worksheet = workbook[sheet]
                    processed = False
                    # 遍历每个单元格
                    for row in worksheet.iter_rows(min_row=1, max_col=worksheet.max_column, max_row=worksheet.max_row):
                        for cell in row:
                            if isinstance(cell.value, str) and has_japanese(cell.value):
                                # 处理日文内容
                                new_value = del_japanese_prompt(0.1, cell.value, [])
                                processed = True
                                cell_value = str(cell.value).replace("\n", "")
                                new_cell_value = str(new_value).replace("\n", "")
                                await manager.send_personal_message(json.dumps({
                                    "content": f'''
                                    修正：
                                    - **シート**: {sheet} ，**行**: {cell.row} ，**列**: {get_column_letter(cell.column)}
                                    - **修正前**: {cell_value}
                                    - **修正後**: {new_cell_value}
                                '''
                                }, ensure_ascii=False), websocket)
                                cell.value = new_value
                    # 如果工作表被处理，保存修改
                    if processed:
                        workbook.save(new_file_path)
                put_file("modify-ja-file", f"{file_dir}.{file_type}", new_file_path)
                shutil.rmtree(f"./data/{file_dir}")
                await manager.send_personal_message(json.dumps({
                    "old_file_name": object_name,
                    "new_file_name": f"{file_dir}.{file_type}",
                    "bucket_name": "modify-ja-file"
                }, ensure_ascii=False), websocket)
            if file_type == 'txt':
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
                text_array = text.split("\n\n")
                for index, item in enumerate(text_array):
                    if has_japanese(item):
                        ai_value = del_japanese_prompt(0.1, item, [])
                        aisay_item = item.replace("\n", "")
                        aisay_value = ai_value.replace("\n", "")
                        text_array[index] = ai_value  # 替换原始文本数组中的值
                        await manager.send_personal_message(json.dumps({
                            "content": f'''
                               修正：
                               - **修正前**: {aisay_item}
                               - **修正後**: {aisay_value}
                           '''
                        }, ensure_ascii=False), websocket)

                # 将修改后的文本数组重新组合成字符串
                new_text = '\n\n'.join(text_array)
                # 指定一个绝对路径
                output_path = f'./data/new_{file_dir}.{file_type}'
                # 创建一个txt文件，写入new_text
                with open(output_path, 'w', encoding='utf-8') as output_file:
                    output_file.write(new_text)
                put_file("modify-ja-file", f"new_{file_dir}.{file_type}", output_path)
                await manager.send_personal_message(json.dumps({
                    "old_file_name": object_name,
                    "new_file_name": f"new_{file_dir}.{file_type}",
                    "bucket_name": "modify-ja-file"
                }, ensure_ascii=False), websocket)
            if file_type == 'doc' or file_type == 'docx':
                replacements = {}
                red_list = get_red_text_from_docx(file_path)
                if len(red_list) > 0:
                    for index, item in enumerate(red_list):
                        ai_value = del_japanese_prompt(0.1, item, [])
                        aisay_item = item.replace("\n", "")
                        aisay_value = ai_value.replace("\n", "")
                        replacements[item] = ai_value
                        await manager.send_personal_message(json.dumps({
                            "content": f'''
                            修正：
                            - **修正前**: {aisay_item}
                            - **修正後**: {aisay_value}
                        '''
                        }, ensure_ascii=False), websocket)
                        replace_text_in_docx(file_path, replacements, new_file_path)
                    # 返回新文件的内容
                    with open(new_file_path, "rb") as file:
                        file_contents = file.read()
                    os.remove(new_file_path)
                    await manager.send_personal_message(json.dumps({
                        "old_file_name": object_name,
                        "new_file_name": new_file_path,
                        "bucket_name": "modify-ja-file"
                    }, ensure_ascii=False), websocket)
                else:
                    await manager.send_personal_message(json.dumps({
                        "content": f'''翻訳が必要なテキストは検出されませんでした'''
                    }, ensure_ascii=False), websocket)
        except Exception as e:
            print(e)
        finally:
            manager.disconnect(websocket)

    # 文件对话##############################################################
    @app.post("/file_chat/upload")
    def file_chat_upload(file: Filechat1):
        try:
            user_id = "_"+file.userid
            milvus_list = get_milvus_collections_info()
            is_in_name = any(item['name'] == user_id for item in milvus_list)
            file_type = os.path.splitext(file.object_name)[1]
            if file_type == 'pdf':
                content_list = parse_file_pdf(file.bucket_name, file.object_name)
            else:
                content_list = parse_file_other(file.bucket_name, file.object_name)
            if is_in_name:
                del_entity(user_id)
            else:
                create_milvus(user_id, "")
            for item in content_list:
                if item is None:
                    continue
                data = [{
                    'text': item,
                    'embeddings': bg3_m3(item),
                    'file_name': file.object_name
                }]
                insert_milvus(data, user_id)
            return ResponseEntity(
                        message="success",
                        status_code=200
                    )
        except Exception as e:
            print(e)
            return ResponseEntity(
                message="error",
                status_code=500
            )

    @app.websocket("/file_chat/qa/{v1}")
    async def file_chat_qa(websocket: WebSocket, v1: str):
        manager = ConnectionManager()
        await manager.connect(websocket)
        try:
            data = await websocket.receive_text()
            params = Filechat2.parse_raw(data)
            question = params.question
            history = params.history
            user_id = "_"+params.userid
            language = params.language
            res = matching_paragraph(question, user_id, 1000)
            filtered_result = []
            for result in res:
                filtered_result = [res.entity.text for res in result if res.score > 0]
            a = rerank(question, filtered_result, 3)
            rerank_results = [y['index'] for y in a if y['relevance_score'] > 0.7]
            rerank_filtered_result = []
            for index in rerank_results:
                rerank_filtered_result.append(filtered_result[index])
            message = {"content": file_chat_prompt.format(question=question, content=str(rerank_filtered_result),
                                                          language=language), "role": "user"}
            history.append(message)
            answer = glm4_9b_chat_ws(history, 0.7)
            for chunk in answer:
                await manager.send_personal_message(json.dumps({
                    "answer": chunk.choices[0].delta.content
                }, ensure_ascii=False), websocket)
        except Exception as e:
            print(e)
        finally:
            manager.disconnect(websocket)

    return app


app = init_flask()
uvicorn.run(app, host='0.0.0.0', port=8001, workers=1, timeout_keep_alive=300)
