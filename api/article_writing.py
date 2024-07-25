from knowledge.dataset_api import matching_paragraph
from llm.embeddings import rerank
from llm.glm4 import glm4_9b_chat, glm4_9b_chat_http

prompt = '''
请你根据用户的要求，以及参考资料帮我生成一篇中文论文大纲，最后以严格的json格式返回(不要丢失括号)，不需要解释，大标题和小标题都要有序号，大标题需要用大写序号。
用户要求：{{query}}
参考资料：{{ref}}

json格式要求：
{
  "标题": "",
  "摘要": "",
  "关键词": "",
  "正文": [
    {
      "标题": "第一章 XXXXX",
      "内容": "章节1详细内容",
      "小节": [
        {
          "小节标题": "1.1 小节标题",
          "内容": "1.1 小节内容"
        },
        {
          "小节标题": "1.2 小节标题",
          "内容": "1.2 小节内容"
        }
      ]
    },
    {
      "标题": "第二章 XXXXX",
      "内容": "章节2详细内容",
      "小节": [
        {
          "小节标题": "2.1 小节标题",
          "内容": "2.1 小节内容"
        },
        {
          "小节标题": "2.2 小节标题",
          "内容": "2.2 小节内容"
        }
        // 更多小节...
      ]
    }
    // 更多章节...
  ]
}
'''
article_prompt = '''
你是论文撰写专家，请你根据我提供的参考资料以及论文大纲，帮我扩写这篇论文的摘要，不需要解释，只返回摘要的内容，请不要撰写关键词，不得少于300字。

参考资料：{{ref}}

论文大纲：{{outline}}
'''
body_prompt = '''
你是论文撰写专家（善于用数学公式以及表格辅助说明），我将提供给你参考资料，论文大纲以及需要你编写的小节部分。
你需要做的是阅读并理解这些内容，然后根据我的要求，帮助我生成小节的内容。

要求：
    1. 请不要在内容中参杂标题，全写正文。
    2. 不需要多余的解释。
    3. 小节内容要丰富。
    4. 所有的数学公式请用 LaTeX 语法来展示，例如：$$ E = mc^2 $$，请确保LaTeX语法的正确性。
    5. 不得少于500字。
    6. 在小节最后不需要你总结。
    7. 请不要在正文中添加引用。


需要你编写的：{{type}}

参考资料：{{ref}}

论文大纲：{{outline}}
'''
revise_prompt = '''
你是论文撰写专家，我将提供给你一个需要修改的论文正文片段，请你根据我的要求进行修改。

默认要求：
        1. 请不要在内容中参杂标题，全写正文。
        2. 不需要多余的解释。
        3. 小节内容要丰富。
        4. 所有的数学公式请用 LaTeX 语法来展示，例如：$$ E = mc^2 $$。
        5. 不得少于500字。

追加要求：
        {{query}}

论文正文片段：
        {{content}}
'''


def get_ref(query):
    ref = matching_paragraph(query, 'damage_explosion_v1', 1000)
    filtered_results = []
    for result in ref:
        filtered_result = [res.entity.text for res in result if res.score > 0]
        filtered_results.append(filtered_result)
    a = rerank(query, filtered_results[0], 5)
    rerank_results = [y['index'] for y in a if y['relevance_score'] > 0.7]
    rerank_filtered_result_text = []
    rerank_filtered_result_file = []
    for index in rerank_results:
        rerank_filtered_result_text.append(ref[0][index].fields['text'] + '\n')
        rerank_filtered_result_file.append(ref[0][index].fields['file_name'])
    return rerank_filtered_result_text, set(rerank_filtered_result_file)
def extract_bracket_content(s):
    start = s.find('{')
    end = s.rfind('}')
    if start == -1 or end == -1 or start > end:
        return ""  # 如果找不到大括号或者顺序不正确，返回空字符串
    return s[start:end + 1]

def get_outline(query, temperature):
    rerank_filtered_result, rerank_filtered_result_file = get_ref(query)
    messages = [
        {"content": prompt.replace("{{query}}", query).replace("{{ref}}", str(rerank_filtered_result)), "role": "user"}]
    ai_say = glm4_9b_chat_http(messages,temperature)

    return {
        'json': extract_bracket_content(ai_say),
        'ref_file': rerank_filtered_result_file
    }
