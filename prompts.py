from llm.glm4 import glm4_9b_chat_http


def del_japanese_prompt(temperature, prompt, history):
    # '私はあなたが日本語の翻訳、校正修辞の改善の役を担当することを望んでいます。\
    # 私はどんな言語であなたと交流することができて、あなたは言語を識別することができて、\
    # それを翻訳してそしてもっと正確で合理的な日本語で私に答えることができます。\
    # 私の標準ではない日本語の文をより標準的な尊敬の表現に修正して、意味が変わらないようにしてください。\
    # 修正した文をそのまま返します！！！！\n'
    system = '''
            '我希望你能担当日语校对改进的角色。\n
             我只用日语和你交流，你要用最准确合理的日语回答我。\n
             把我不标准的日语句子修改成没有拼写和语法错误、地道的标准日语，并且意思不要改变，尽可能和原句保持一致。\n
             如果有数字和符号，请不要修改。\n
             请只返回我修改后的句子，不要其他多余的解释!!!'
    '''
    history.insert(0, {"role": "system", "content": system})
    history.append({"role": "user", "content": prompt})
    return glm4_9b_chat_http(history, temperature)