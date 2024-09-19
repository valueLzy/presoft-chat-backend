from typing import Any, List
import requests
from llama_index.core.bridge.pydantic import PrivateAttr
from llama_index.core.embeddings import BaseEmbedding


class InstructorEmbeddings(BaseEmbedding):
    _url: str = PrivateAttr()
    _instruction: str = PrivateAttr()

    def __init__(
        self,
        url: str = "http://192.168.2.8:8001/v1/embeddings",
        instruction: str = '''
        ''',
        **kwargs: Any,
    ) -> None:
        self._url = url
        self._instruction = instruction
        super().__init__(**kwargs)

    @classmethod
    def class_name(cls) -> str:
        return "instructor"

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._get_text_embedding(text)

    def _get_query_embedding(self, query: str) -> List[float]:
        return self._get_embedding(query)

    def _get_text_embedding(self, text: str) -> List[float]:
        return self._get_embedding(text)

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self._get_embedding(text) for text in texts]

    def _get_embedding(self, input_text: str) -> List[float]:
        response = requests.post(
            self._url,
            json={
                "model": "bge-m3",
                "input": input_text
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]
