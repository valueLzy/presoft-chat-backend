import json
import os
import shutil
import uuid
from datetime import datetime

import openpyxl
import uvicorn
from fastapi import FastAPI, WebSocket
from llama_index.core import Settings, SimpleDirectoryReader, StorageContext, KnowledgeGraphIndex
from llama_index.core.graph_stores import SimpleGraphStore
from openpyxl.utils import get_column_letter
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from api.article_writing import get_outline, get_summary, get_keywords, extract_content_from_json, get_body, \
    list_to_query, revise_article
from database.graph_ngql import create_nebula_space_and_schema, drop_space
from database.sql import get_user_with_menus, check_username_exists, insert_user, insert_knowledge, \
    get_knowledge_by_user, delete_knowledge_by_name_and_user, insert_history_qa, query_history_by_user_and_type, \
    insert_knowledge_file, query_knowledge_file_by_knowledge_id_and_file_name, delete_knowledge_file_by_name_and_file
from knowledge.dataset_api import matching_paragraph
from llm.embeddings import bg3_m3, rerank

from llm.glm4 import glm4_9b_chat_ws, glm4_9b_chat_long_http
from llm.glm4_llamaindex import GLM4
from llm.llama_index_embeddings import InstructorEmbeddings
from llm.zhipuai_llamaindex import BianCangLLM
from milvus.milvus_tools import create_milvus, insert_milvus, get_milvus_collections_info, del_entity, \
    get_unique_field_values, delete_milvus, del_entity_by_file, query_milvus_by_file_name
from prompt import file_chat_prompt
from prompts import del_japanese_prompt, del_japanese_prompt_ws
from util.websocket_utils import ConnectionManager
from utils import md5_encrypt, download_file, put_file, has_japanese, get_red_text_from_docx, \
    replace_text_in_docx, parse_file_other, parse_file_pdf, matching_milvus_paragraph, get_graph
from models.entity import Question, UserLogin, UserRegister, Basic, Article, Edit, JachatCorrect, \
    JafileCorrect, Filechat1, Filechat2, ResponseEntity, Knowledge, GetKnowledge, DelKnowledge, KnowledgeQa, \
    KnowledgeFile, KnowledgeFileDel, KnowledgeFileUpload, HistoryList, KnowledgeFileList


def init_flask():
    Settings.embed_model = InstructorEmbeddings()
    Settings.llm = BianCangLLM()

    documents = SimpleDirectoryReader(f"./xiaoming/").load_data()

    graph_store = SimpleGraphStore()

    storage_context = StorageContext.from_defaults(graph_store=graph_store)

    index = KnowledgeGraphIndex.from_documents(documents=documents,
                                               max_triplets_per_chunk=3,
                                               storage_context=storage_context,
                                               include_embeddings=True)
    app = FastAPI()
    #前端跨域 添加 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许所有来源，或者指定特定的源列表
        allow_credentials=True,
        allow_methods=["*"],  # 允许所有方法（如GET、POST等）
        allow_headers=["*"],  # 允许所有请求头
    )

    # 登录
    @app.post("/api/user/login")
    def login(user: UserLogin):
        print(user)
        # 获取用户及其菜单信息
        result = get_user_with_menus(user.username, md5_encrypt(user.password), user.language)

        if not result:
            return JSONResponse(status_code=404, content={"message": "用户名或密码不存在"})

        # 提取用户信息和菜单信息
        user_info = result["user_info"]
        menu_list = result["menuList"]
        tokenstr = user_info[0] + user.username + user.password
        # 生成Token
        token = md5_encrypt(tokenstr)
        # 构建返回的数据结构
        return JSONResponse(content={
            "userId": user_info[0],
            "userName": user_info[1],
            "roles": user_info[2],
            "desc": user_info[3],
            "password": user_info[4],
            "menuList": menu_list,
            "token": token
        })

    # 注册
    @app.post("/api/user/register")
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

    @app.post("/api/history/get_list")
    def get_history_list(history: HistoryList):
        try:
            res = query_history_by_user_and_type(history.user_id, history.type)
            history = []
            for item in res:
                data = [
                    {"role": "user", "content": item[0]},
                    {"role": "assistant", "content": item[1]},
                    {"time": item[2]}
                ]
                history.append(data)
            return ResponseEntity(
                message=history,
                status_code=200
            )
        except Exception as e:
            return ResponseEntity(
                message=str(e),
                status_code=500
            )

    # 普通对话
    @app.websocket("/api/common_chat/{v1}")
    async def common_chat(websocket: WebSocket, v1: str):

        manager = ConnectionManager()
        await manager.connect(websocket)
        try:
            data = await websocket.receive_text()
            params = Question.parse_raw(data)
            print(params)
            prompt = params.prompt
            history = params.history
            history.append({"content": prompt, "role": "user"})
            temperature = params.temperature
            aaa = ""
            answer = glm4_9b_chat_ws(history, temperature)
            for chunk in answer:
                aaa += str(chunk.choices[0].delta.content)
                print(aaa)
                await manager.send_personal_message(json.dumps({
                    "answer": chunk.choices[0].delta.content
                }, ensure_ascii=False), websocket)
            insert_history_qa(v1, prompt, aaa, "dialog")
        except Exception as e:
            print(e)
        finally:
            manager.disconnect(websocket)

    # 论文---获取关键词
    @app.post("/api/write/get_keywords")
    def get_write_keywords():
        try:
            res = get_unique_field_values("damage_explosion_v2", "type")
            keywords_list = [{"name": item, "checked": False} for item in res]
            return ResponseEntity(
                message=keywords_list,
                status_code=200
            )
        except Exception as e:
            return ResponseEntity(
                message=str(e),
                status_code=500
            )

    # 论文---生成大纲
    @app.post("/api/write/get_basic")
    def get_basic(basic: Basic):
        print(basic)
        return get_outline(basic.article_title, 0.7, list_to_query(basic.article_choices))

    # 论文---生成论文
    @app.websocket("/api/write/get_article/{v1}")
    async def get_article(websocket: WebSocket, v1: str):
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

    # 论文---修改章节
    @app.websocket("/api/write/edit_article/{v1}")
    async def edit_article(websocket: WebSocket, v1: str):
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

    # 日语修正-对话
    @app.websocket("/api/correctJa/chat/{v1}")
    async def correct_ja_chat(websocket: WebSocket, v1: str):
        manager = ConnectionManager()
        await manager.connect(websocket)
        try:
            data = await websocket.receive_text()
            params = JachatCorrect.parse_raw(data)
            prompt = params.prompt
            answer = del_japanese_prompt_ws(prompt)
            ai_say = ""
            for chunk in answer:
                ai_say += chunk.choices[0].delta.content
                await manager.send_personal_message(json.dumps({
                    "answer": chunk.choices[0].delta.content
                }, ensure_ascii=False), websocket)
            insert_history_qa(v1, prompt, ai_say, "revise")
        except Exception as e:
            print(e)
        finally:
            manager.disconnect(websocket)

    # 日语修正-文件
    @app.websocket("/api/correctJa/file/{v1}")
    async def correct_ja_file(websocket: WebSocket, v1: str):
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
                                    修正：<br>
                                    <b>シート<b/>: {sheet} ，**行**: {cell.row} ，**列**: {get_column_letter(cell.column)}<br>
                                    <b>修正前<b/>: {cell_value}<br>
                                    <b>修正後<b/>: {new_cell_value}<br>
                                '''
                                }, ensure_ascii=False), websocket)
                                insert_history_qa(v1, "日语修正-excel", f'''
                                    修正：<br>
                                    <b>シート<b/>: {sheet} ，**行**: {cell.row} ，**列**: {get_column_letter(cell.column)}<br>
                                    <b>修正前<b/>: {cell_value}<br>
                                    <b>修正後<b/>: {new_cell_value}<br>
                                ''', "revise")
                                cell.value = new_value
                    # 如果工作表被处理，保存修改
                    if processed:
                        workbook.save(new_file_path)
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
                               <b>修正<b/>：<br>
                               <b>修正前<b/>: {aisay_item}<br>
                               <b>修正後<b/>: {aisay_value}
                           '''
                        }, ensure_ascii=False), websocket)
                        insert_history_qa(v1, "日语修正-txt", f'''
                               <b>修正<b/>：<br>
                               <b>修正前<b/>: {aisay_item}<br>
                               <b>修正後<b/>: {aisay_value}
                           ''', "revise")
                # 将修改后的文本数组重新组合成字符串
                new_text = '\n\n'.join(text_array)
                # 指定一个绝对路径
                output_path = f'./data/new_{file_dir}.{file_type}'
                # 创建一个txt文件，写入new_text
                with open(output_path, 'w', encoding='utf-8') as output_file:
                    output_file.write(new_text)
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
                            <b>修正<b/>：<br>
                            <b>修正前<b/>: {aisay_item}<br>
                            <b>修正後<b/>: {aisay_value}
                        '''
                        }, ensure_ascii=False), websocket)
                        insert_history_qa(v1, "日语修正-word", f'''
                            <b>修正<b/>：<br>
                            <b>修正前<b/>: {aisay_item}<br>
                            <b>修正後<b/>: {aisay_value}
                        ''', "revise")
                        replace_text_in_docx(file_path, replacements, new_file_path)
                else:
                    await manager.send_personal_message(json.dumps({
                        "content": f'''翻訳が必要なテキストは検出されませんでした'''
                    }, ensure_ascii=False), websocket)
            put_file("modify-ja-file", f"{file_dir}.{file_type}", new_file_path)
            shutil.rmtree(f"./data/{file_dir}")
            await manager.send_personal_message(json.dumps({
                "old_file_name": object_name,
                "new_file_name": f"{file_dir}.{file_type}",
                "bucket_name": "modify-ja-file"
            }, ensure_ascii=False), websocket)
            insert_history_qa(v1, "修改后-下载文件", f"192.168.1.21:19000/modify-ja-file/{file_dir}.{file_type}", "revise")
        except Exception as e:
            print(e)
        finally:
            manager.disconnect(websocket)

    # 文件对话-上传文件
    @app.post("/api/file_chat/upload")
    def file_chat_upload(file: Filechat1):
        try:
            user_id = "_" + file.userid
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

    # 文件对话-用户对话
    @app.websocket("/api/file_chat/qa/{v1}")
    async def file_chat_qa(websocket: WebSocket, v1: str):
        manager = ConnectionManager()
        await manager.connect(websocket)
        try:
            data = await websocket.receive_text()
            params = Filechat2.parse_raw(data)
            question = params.question
            history = params.history
            user_id = "_" + params.userid
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
            ai_say = ""
            for chunk in answer:
                ai_say += chunk.choices[0].delta.content
                await manager.send_personal_message(json.dumps({
                    "answer": chunk.choices[0].delta.content
                }, ensure_ascii=False), websocket)
            insert_history_qa(v1, question, ai_say, "fileDialog")
        except Exception as e:
            print(e)
        finally:
            manager.disconnect(websocket)

    # 知识库-获取知识库列表
    @app.post("/api/knowledge/get_list")
    def get_knowledge_list(knowledge: GetKnowledge):
        keys = ['id', 'name', 'description', 'milvus_name', 'graph_name', 'user_id', 'create_time']
        knowledge_list = get_knowledge_by_user(knowledge.userid)
        result = []
        for item in knowledge_list:
            result.append(dict(zip(keys, item)))
        return ResponseEntity(
            message=result,
            status_code=200
        )

    # 知识库-新建知识库
    @app.post("/api/knowledge/create_database")
    def create_knowledge(knowledge: Knowledge):
        try:
            res = get_knowledge_by_user(knowledge.userid)
            second_elements = [item[1] for item in res]
            if knowledge.name in second_elements:
                return ResponseEntity(
                    message="知识库名称已存在！",
                    status_code=501
                )
            knowledge_name = knowledge.name + "_" + knowledge.userid
            # 创建milvus
            create_milvus(knowledge_name, knowledge.description)
            # 创建graph
            create_nebula_space_and_schema(knowledge_name)
            # 插入mysql
            insert_knowledge(str(uuid.uuid4()), knowledge.name, knowledge.description, knowledge_name, knowledge_name,
                             knowledge.userid, datetime.now())
            return ResponseEntity(
                message="success",
                status_code=200
            )
        except Exception as e:
            return ResponseEntity(
                message="error",
                status_code=500
            )

    # 知识库-删除知识库
    @app.post("/api/knowledge/drop_database")
    def drop_knowledge(knowledge: DelKnowledge):
        try:
            mg_name = knowledge.name + "_" + knowledge.userid
            drop_space(mg_name)
            delete_milvus(mg_name)
            delete_knowledge_by_name_and_user(knowledge.name, knowledge.userid)
            return ResponseEntity(
                message="success",
                status_code=200
            )
        except Exception as e:
            return ResponseEntity(
                message="error",
                status_code=500
            )

    # 对话-知识库
    @app.websocket("/api/knowledge/qa/{v1}")
    async def knowledge_qa(websocket: WebSocket, v1: str):
        manager = ConnectionManager()
        await manager.connect(websocket)
        try:
            data = await websocket.receive_text()
            params = KnowledgeQa.parse_raw(data)
            history = params.history
            question = params.question
            knowledge_name = params.knowledge_name
            user_id = params.userid
            ai_say = ""
            if knowledge_name == "xiaoming":
                query_engine = index.as_query_engine(include_text=True,
                                                     response_mode="tree_summarize",
                                                     embedding_mode="hybrid",
                                                     similarity_top_k=4,
                                                     streaming=True)
                generator = query_engine.query(question).response_gen
                for chunk in generator:
                    # 在这里处理每个块
                    await manager.send_personal_message(json.dumps({
                        "answer": chunk
                    }, ensure_ascii=False), websocket)
            else:
                res = matching_milvus_paragraph(question, knowledge_name, 3)
                messages = {"content": file_chat_prompt.format(question=question, content=str(res), language='中文'),
                            "role": "user"}
                history.append(messages)
                answer = glm4_9b_chat_ws(history, 0.1)
                for chunk in answer:
                    ai_say += chunk.choices[0].delta.content
                    await manager.send_personal_message(json.dumps({
                        "answer": chunk.choices[0].delta.content
                    }, ensure_ascii=False), websocket)
            insert_history_qa(v1, question, ai_say, "questions")
        except Exception as e:
            print(e)
        finally:
            manager.disconnect(websocket)

    # 知识库-获取知识库内文件列表
    @app.post("/api/knowledge/get_files")
    def get_files(knowledge: KnowledgeFile):
        try:
            res = get_unique_field_values(knowledge.knowledge_name + "_" + knowledge.user_id, "file_name")
            return ResponseEntity(
                message=res,
                status_code=200
            )
        except Exception as e:
            return ResponseEntity(
                message=e,
                status_code=500
            )

    # 知识库-知识库内文件列表删除
    @app.post("/api/knowledge/del_file")
    def del_file(knowledge: KnowledgeFileDel):
        try:
            knowledge_name = knowledge.knowledge_name + "_" + knowledge.user_id
            del_entity_by_file(knowledge_name, knowledge.file_name)
            delete_knowledge_file_by_name_and_file(knowledge_name, knowledge.file_name)
            return ResponseEntity(
                message="success",
                status_code=200
            )
        except Exception as e:
            return ResponseEntity(
                message=e,
                status_code=500
            )

    # 知识库-知识库内文件上传
    @app.post("/api/knowledge/upload_file")
    def upload_file(knowledge: KnowledgeFileUpload):
        try:
            knowledge_name = knowledge.knowledge_name + "_" + knowledge.user_id
            file_name = knowledge.minio_file_name
            bucket_name = knowledge.minio_bucket_name
            file_type = os.path.splitext(file_name)[1]
            if file_type == '.pdf':
                text_splitter = parse_file_pdf(bucket_name, file_name)
            else:
                text_splitter = parse_file_other(bucket_name, file_name)
            for text in text_splitter:
                data = [{
                    'text': text,
                    'file_name': knowledge.file_name,
                    'embeddings': bg3_m3(text)
                }]
                insert_milvus(data, knowledge_name)
            prompt = f"""
            {text_splitter}\n\t
            请你帮我总结上述文本中的大纲，结果不要超过100字，只返回大纲，不需要多余的解释。
            """
            message = [{"content": prompt, "role": "user"}]
            graph_html = get_graph(bucket_name, file_name)
            outline = "1"
            insert_knowledge_file(knowledge_name, knowledge.file_name, graph_html, outline)
            return ResponseEntity(
                message="success",
                status_code=200
            )
        except Exception as e:
            return ResponseEntity(
                message=e,
                status_code=500
            )

    # 知识库-文件内列表
    @app.post("/api/knowledge/file_list")
    def get_file_list(knowledge: KnowledgeFileList):
        try:
            knowledge_name = knowledge.knowledge_name + "_" + knowledge.user_id
            file_name = knowledge.file_name
            text_splitter = query_milvus_by_file_name(knowledge_name, file_name)
            graph = query_knowledge_file_by_knowledge_id_and_file_name(knowledge_name, file_name)
            res = {
                "text_splitter": text_splitter,
                "graph": graph
            }
            return ResponseEntity(
                message=res,
                status_code=200
            )
        except Exception as e:
            return ResponseEntity(
                message=e,
                status_code=500
            )

    return app


app = init_flask()
uvicorn.run(app, host='0.0.0.0', port=8001, workers=1)
