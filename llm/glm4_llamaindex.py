from typing import List, Optional

import requests
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from langchain.llms.utils import enforce_stop_tokens


class GLM4(LLM):
    history = []

    def __init__(self):
        super().__init__()

    @property
    def _llm_type(self) -> str:
        return "qwen1"

    def _call(self, prompt: str, stop: Optional[List[str]] = None,
              run_manager: Optional[CallbackManagerForLLMRun] = None) -> str:
        headers = {
            "Authorization": f"Bearer f9bb07bb045c3e1c033fb1fa532eadc7.WIW3tMk0zG0SCjym"
        }
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        data = {
            "model": "glm-4-0520",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 200:
            return "error"
        resp = response.json()['choices'][0]['message']['content']
        if stop is not None:
            response = enforce_stop_tokens(resp, stop)
        self.history = self.history + [[None, resp]]
        return resp
