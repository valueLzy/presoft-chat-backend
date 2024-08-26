from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any


class ResponseEntity(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    status_code: int
    message: any


class Question(BaseModel):
    prompt: str
    history: List[dict[str, str]]
    temperature: float


class UserLogin(BaseModel):
    username: str
    password: str
    language: str


class UserRegister(BaseModel):
    username: str
    password: str
    company: str
    nationality: str


class Basic(BaseModel):
    article_title: str
    article_choices: list


class Article(BaseModel):
    article_base: Dict[str, Any]
    article_choices: list


class Edit(BaseModel):
    oldpart: str
    prompt: str


class JafileCorrect(BaseModel):
    bucket_name: str
    object_name: str


class JachatCorrect(BaseModel):
    prompt: str


class Filechat1(BaseModel):
    bucket_name: str
    object_name: str
    userid: str


class Filechat2(BaseModel):
    history: List[dict[str, str]]
    question: str
    userid: str
    language: str


class Knowledge(BaseModel):
    name: str
    description: str
    userid: str


class GetKnowledge(BaseModel):
    userid: str


class DelKnowledge(BaseModel):
    userid: str
    name: str


class KnowledgeQa(BaseModel):
    history: List[dict[str, str]]
    question: str
    userid: str
    knowledge_name: str


class KnowledgeFile(BaseModel):
    knowledge_name: str


class KnowledgeFileDel(BaseModel):
    knowledge_name: str
    file_name: str


class KnowledgeFileUpload(BaseModel):
    knowledge_name: str
    bucket_name: str
    file_name: str


class HistoryList(BaseModel):
    user_id: str
    type: str
