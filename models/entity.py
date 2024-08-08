from pydantic import BaseModel
from typing import List, Dict, Any



class ResponseEntity(BaseModel):
    status_code: int
    message: str


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
    article_base: list


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

class Knowledgeinformation(BaseModel):
    name: str
    description: str