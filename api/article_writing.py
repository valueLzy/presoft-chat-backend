from knowledge.dataset_api import matching_paragraph, matching_paragraph_lunwen
from llm.embeddings import rerank
from llm.glm4 import glm4_9b_chat_ws, glm4_9b_chat_http, deepseek_chat

shanhuyun_prompt = '''
请你根据用户的要求，以及参考资料帮我生成一篇中文科技研究报告大纲，最后以严格的json格式返回(不要丢失括号)，不需要解释，大标题和小标题都要有序号，大标题需要用大写序号。
用户要求：{{query}}
参考资料：{{ref}}

json格式要求：
{
  "标题": "",
  "摘要": "",
  "正文": [
    {
      "标题": "第一章 研究背景及现状",
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
      "标题": "第二章 最新研究进展",
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
},
{
      "标题": "第三章 热点问题讨论",
      "内容": "章节3详细内容",
      "小节": [
        {
          "小节标题": "3.1 小节标题",
          "内容": "3.1 小节内容"
        },
        {
          "小节标题": "3.2 小节标题",
          "内容": "3.2 小节内容"
        }
        // 更多小节...
      ]
    }
    // 更多章节...
  ]
},
{
      "标题": "第四章 发展趋势展望",
      "内容": "章节4详细内容",
      "小节": [
        {
          "小节标题": "4.1 小节标题",
          "内容": "4.1 小节内容"
        },
        {
          "小节标题": "4.2 小节标题",
          "内容": "4.2 小节内容"
        }
        // 更多小节...
      ]
    }
    // 更多章节...
  ]
},
{
      "标题": "第五章 结论与建议",
      "内容": "章节5详细内容",
      "小节": [
        {
          "小节标题": "5.1 小节标题",
          "内容": "5.1 小节内容"
        },
        {
          "小节标题": "5.2 小节标题",
          "内容": "5.2 小节内容"
        }
        // 更多小节...
      ]
    }
    // 更多章节...
  ]
}
'''
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
shanhuyun_body_prompt = '''
你是科技研究报告撰写专家（善于用数学公式以及表格辅助说明），我将提供给你参考资料，大纲以及需要你编写的小节部分。
你需要做的是阅读并理解这些内容，然后根据我的要求，帮助我生成小节的内容。

要求：
    1. 请不要在内容中参杂标题，全写正文。
    2. 不需要多余的解释。
    3. 小节内容要丰富。
    4. 不得少于500字。
    5. 在小节最后不需要你总结。
    6. 请不要在正文中添加引用。


需要你编写的：{{type}}

参考资料：{{ref}}

论文大纲：{{outline}}
'''

def get_ref(query, filter_expr):
    ref = matching_paragraph_lunwen(query, 'damage_explosion_v2', 100, filter_expr)
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


#标题获取大纲
def get_outline(query, temperature, filter_expr):
    rerank_filtered_result, rerank_filtered_result_file = get_ref(query, filter_expr)
    messages = [
        {"content": prompt.replace("{{query}}", query).replace("{{ref}}", str(rerank_filtered_result)), "role": "user"}]
    ai_say = glm4_9b_chat_http(messages, temperature)
    print(extract_bracket_content(ai_say), rerank_filtered_result_file)
    return extract_bracket_content(ai_say)


def get_outline_by_shanhuyun(query, temperature, filter_expr):
    rerank_filtered_result, rerank_filtered_result_file = get_ref(query, filter_expr)
    messages = [
        {"content": shanhuyun_prompt.replace("{{query}}", query).replace("{{ref}}", str(rerank_filtered_result)), "role": "user"}]
    ai_say = glm4_9b_chat_http(messages, temperature)
    print(extract_bracket_content(ai_say), rerank_filtered_result_file)
    return extract_bracket_content(ai_say)


#获取摘要
def get_summary(outline, filter_expr):
    abstract = outline['摘要']
    abstract_ref, rerank_filtered_result_file = get_ref(abstract, filter_expr)
    abstract_ref_str = ''
    for item in abstract_ref:
        abstract_ref_str += item + "\n"
    messages = [
        {"content": article_prompt.replace("{{ref}}", abstract_ref_str).replace(
            "{{outline}}", str(outline)),
            "role": "user"}]
    ai_say = glm4_9b_chat_ws(messages, 0.7)
    return {
        'ai_say': ai_say,
        'ref_file': rerank_filtered_result_file
    }


#获取关键词
def get_keywords(outline):
    keywords = outline['关键词']
    return keywords


#从大纲里摘出正文
def extract_content_from_json(json_object):
    # 定义一个数组来存储所有部分的内容
    all_content = []

    # 定义一个函数来处理每个部分
    def process_section(section):
        # 提取标题和内容
        title = section['标题']
        content = section['内容']
        all_content.append({"标题": title, "内容": content})

        # 如果有小节，递归处理每个小节
        if section['小节']:
            for sub_section in section['小节']:
                process_subsection(sub_section)

    # 定义一个函数来处理每个小节
    def process_subsection(sub_section):
        # 提取小节标题和内容
        sub_title = sub_section['小节标题']
        sub_content = sub_section['内容']
        all_content.append({"小节标题": sub_title, "内容": sub_content})

    # 开始处理正文部分
    for section in json_object['正文']:
        process_section(section)

    return all_content


#分小节获取正文
def get_body(outline, type, filter_expr):
    abstract_ref, rerank_filtered_result_file = get_ref(type, filter_expr)
    abstract_ref_str = ''
    for item in abstract_ref:
        abstract_ref_str += item + "\n"
    messages = [
        {"content": body_prompt.replace("{{ref}}", abstract_ref_str).replace(
            "{{outline}}", str(outline)).replace("{{type}}", type),
         "role": "user"}]
    ai_say = deepseek_chat(1.25, messages)
    return {
        'ai_say': ai_say,
        'ref_file': rerank_filtered_result_file
    }

#分小节获取正文
def shanhuyun_get_body(outline, type, filter_expr):
    abstract_ref, rerank_filtered_result_file = get_ref(type, filter_expr)
    abstract_ref_str = ''
    for item in abstract_ref:
        abstract_ref_str += item + "\n"
    messages = [
        {"content": shanhuyun_body_prompt.replace("{{ref}}", abstract_ref_str).replace(
            "{{outline}}", str(outline)).replace("{{type}}", type),
         "role": "user"}]
    ai_say = deepseek_chat(1.25, messages)
    return {
        'ai_say': ai_say,
        'ref_file': rerank_filtered_result_file
    }

def list_to_query(lst):
    query = ' or '.join([f"type == '{item}'" for item in lst])
    return query


# #修改论文-检查是否存在
# def get_value_if_key_in_dicts(array_of_dicts, key_to_check):
#     """
#     判断一个字符串是否是数组中任意一个字典的键，如果是则返回该字典中对应的值，否则返回空字符串
#
#     :param array_of_dicts: 包含字典的数组
#     :param key_to_check: 需要检查的字符串
#     :return: 如果字符串是任意一个字典的键，返回对应的值；否则返回空字符串
#     """
#     for dictionary in array_of_dicts:
#         if key_to_check in dictionary:
#             return dictionary[key_to_check]
#     return ""

#修改论文-修改片段
def revise_article(content, query):
    messages = [{"content": revise_prompt.replace("{{query}}", query).replace(
        "{{content}}", content), "role": "user"}]
    ai_say = deepseek_chat(1.25, messages)
    return ai_say
