from typing import Any

from llama_index.core.base.llms.types import LLMMetadata, CompletionResponse, CompletionResponseGen
from llama_index.core.llms import CustomLLM
from zhipuai import ZhipuAI
from llama_index.core.llms.callbacks import llm_completion_callback

# 假设 zhipuai 库已经安装并且可以导入
# 如果没有安装，可以使用 pip install zhipuai 进行安装

client = ZhipuAI(api_key="f9bb07bb045c3e1c033fb1fa532eadc7.WIW3tMk0zG0SCjym")  # 填写您自己的APIKey


class BianCangLLM(CustomLLM):
    context_window: int = 99999
    num_output: int = 4095
    model_name: str = "BianCang"

    @property
    def metadata(self) -> LLMMetadata:
        """Get LLM metadata."""
        return LLMMetadata(
            context_window=self.context_window,
            num_output=self.num_output,
            model_name=self.model_name,
        )

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        response = client.chat.completions.create(
            model="glm-4-0520",  # 填写需要调用的模型名称
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        print(response.choices[0].message)
        return CompletionResponse(text=response.choices[0].message.content)

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        resp = client.chat.completions.create(
            model="glm-4-0520",  # 填写需要调用的模型名称
            messages=[
                {"role": "user", "content": prompt}
            ],
            stream=True
        )
        response = ""
        for chunk in resp:
            response += chunk.choices[0].delta.content
            yield CompletionResponse(text=response, delta=chunk.choices[0].delta.content)


# 示例使用
if __name__ == "__main__":
    llm = BianCangLLM()
    print(llm.complete("今天天气"))
