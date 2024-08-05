import hashlib
import os
import uuid

from docx import Document
from docx.shared import RGBColor
from minio import Minio

minio_client = Minio(
    "192.168.1.21:19000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False,
)


def md5_encrypt(password):
    # 创建一个md5哈希对象
    md5 = hashlib.md5()

    # 更新哈希对象以包含密码的二进制数据
    md5.update(password.encode('utf-8'))

    # 获取加密后的十六进制表示
    encrypted_password = md5.hexdigest()

    return encrypted_password


def download_file(bucket_name: str, file_name: str) -> dict[str, str] | str:
    unique_id = str(uuid.uuid4())
    folder_path = f'./data/{unique_id}'
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, file_name)
    try:
        minio_client.fget_object(
            bucket_name=bucket_name,
            object_name=file_name,
            file_path=file_path,
        )
        return {
            "file_path": str(file_path),
            "file_dir": unique_id
        }
    except Exception as e:
        return ""


def put_file(bucket_name: str, file_name: str, file_path: str) -> bool:
    try:
        minio_client.fput_object(
            bucket_name=bucket_name,
            object_name=file_name,
            file_path=file_path,
        )
        return True
    except Exception as e:
        return False


def has_japanese(text: str) -> bool:
    for char in str(text):
        if ('\u3040' <= char <= '\u30FF') or ('\u31F0' <= char <= '\u31FF'):
            return True
    return False

def get_red_text_from_docx(file_path):
    # 打开文档
    doc = Document(file_path)
    red_texts = []

    # 遍历所有段落
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            # 检查字体颜色是否为红色
            if run.font.color and run.font.color.rgb == RGBColor(255, 0, 0):
                red_texts.append(run.text)

    # 遍历所有表格
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        # 检查字体颜色是否为红色
                        if run.font.color and run.font.color.rgb == RGBColor(255, 0, 0):
                            red_texts.append(run.text)

    return red_texts

def replace_text_in_docx(file_path, replacements, new_file_path):
    # 打开文档
    doc = Document(file_path)

    # 遍历所有段落并替换文本
    for paragraph in doc.paragraphs:
        for old_text, new_text in replacements.items():
            if old_text in paragraph.text:
                replace_text_in_paragraph(paragraph, old_text, new_text)

    # 遍历所有表格并替换文本
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for old_text, new_text in replacements.items():
                        if old_text in paragraph.text:
                            replace_text_in_paragraph(paragraph, old_text, new_text)

    # 保存修改后的文档
    doc.save(new_file_path)

def replace_text_in_docx(file_path, replacements, new_file_path):
    # 打开文档
    doc = Document(file_path)

    # 遍历所有段落并替换文本
    for paragraph in doc.paragraphs:
        for old_text, new_text in replacements.items():
            if old_text in paragraph.text:
                replace_text_in_paragraph(paragraph, old_text, new_text)

    # 遍历所有表格并替换文本
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for old_text, new_text in replacements.items():
                        if old_text in paragraph.text:
                            replace_text_in_paragraph(paragraph, old_text, new_text)

    # 保存修改后的文档
    doc.save(new_file_path)


def replace_text_in_paragraph(paragraph, old_text, new_text):
    for run in paragraph.runs:
        if old_text in run.text:
            run.text = run.text.replace(old_text, new_text)
            run.font.color.rgb = RGBColor(72, 116, 203)


if __name__ == '__main__':
    # print(put_file("vue-file", "aaaa.xlsx", "data/aaaa.xlsx"))
    print(put_file("modify-ja-file", "test.docx", "data/test.docx"))
