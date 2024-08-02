from pydantic import BaseModel
from typing import List, Dict, Any


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


class Correct(BaseModel):
    bucket_name: str
    object_name: str
