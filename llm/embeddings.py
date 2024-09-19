import requests


# 定义请求的URL


def bg3_m3(messages):
    # 定义请求体
    url = "http://192.168.2.8:8001/v1/embeddings"
    data = {
        "model": "bge-m3",  # 替换为你使用的模型名
        "input": messages
    }

    # 发起POST请求
    response = requests.post(url, json=data)

    # 处理响应
    if response.status_code == 200:
        result = response.json()
        return result['data'][0]['embedding']
    else:
        return f"请求失败，状态码：{response.status_code}"


def rerank(query, documents, matches_number):
    # 定义请求体
    url = "http://192.168.2.8:6006/v1/rerank"
    data = {
        "query": query,
        "documents": documents
    }

    # 定义请求头
    headers = {
        "Authorization": f"Bearer ACCESS_TOKEN"
    }

    # 发起POST请求
    response = requests.post(url, json=data, headers=headers)

    # 处理响应
    if response.status_code == 200:
        try:
            result = response.json()
            sorted_results = sorted(result['results'], key=lambda x: x['relevance_score'], reverse=True)
            top_three_results = sorted_results[:matches_number]
            return top_three_results
        except Exception as e:
            return documents[:matches_number]
    else:
        return f"请求失败，状态码：{response.status_code}"


def segment_document(text):
    url = "http://192.168.2.8:8506/segment_document"
    data = {
        "document": text
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        result = response.json()
        return result
    else:
        return f"请求失败，状态码：{response.status_code}"


if __name__ == '__main__':
    print(rerank('你好', ['你好', '2', '3', '3', '你好1']))
