import os
import sys

from llama_index.core.chat_engine import CondenseQuestionChatEngine
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.readers.file import PyMuPDFReader

from llm.glm4_llamaindex import GLM4
from llm.llama_index_embeddings import InstructorEmbeddings

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

Settings.embed_model = InstructorEmbeddings()
Settings.llm = GLM4()

# 指定文件夹路径
fusion_retriever = None


def file_upload(uploaded_file, file_path):
    # 当有文件被上传时
    if uploaded_file is not None:
        global fusion_retriever
        # 检查文件夹是否存在
        if os.path.exists(file_path):
            # 遍历文件夹下的所有文件
            for filename in os.listdir(file_path):
                file_path = os.path.join(file_path, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)  # 删除文件
                except Exception as e:
                    print(f'删除 {file_path} 失败. 原因: {e}')
        # 生成保存路径
        save_path = os.path.join(file_path, uploaded_file.name)

        # 将文件保存到指定路径
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        documents = SimpleDirectoryReader("data", file_extractor={".pdf": PyMuPDFReader()}).load_data()
        index = VectorStoreIndex.from_documents(documents)
        # 8. 定义 RAG Fusion 检索器
        fusion_retriever = QueryFusionRetriever(
            [index.as_retriever()],
            similarity_top_k=5,  # 检索召回 top k 结果
            num_queries=4,  # 生成 query 数
            use_async=True,
            # query_gen_prompt="...",  # 可以自定义 query 生成的 prompt 模板
        )
        return "success"


def get_conversations_answer(question):
    global fusion_retriever  # 声明使用全局变量
    if fusion_retriever is None:
        return 'ファイルをまずアップロードしてください。'

    # 9. 构建单轮 query engine
    query_engine = RetrieverQueryEngine.from_args(
        fusion_retriever
    )

    chat_engine = CondenseQuestionChatEngine.from_defaults(
        query_engine=query_engine,
        # condense_question_prompt=... # 可以自定义 chat message prompt 模板
    )

    # 使用index进行查询操作

    response = chat_engine.chat(question)
    return response.response
