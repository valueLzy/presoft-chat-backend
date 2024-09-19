import os


def list_pdfs_in_directory(directory):
    """
    递归遍历指定路径下的所有文件夹，并列出每个文件夹中的所有PDF文件。
    只打印最后一个文件夹的名字。

    :param directory: 要遍历的根目录路径
    """
    # 遍历指定目录下的所有文件和文件夹
    for root, dirs, files in os.walk(directory):
        # 获取当前文件夹的名字
        current_folder_name = os.path.basename(root)

        # 遍历当前文件夹中的所有文件
        for file in files:
            # 检查文件是否是PDF文件
            if file.lower().endswith('.pdf'):
                print(f"当前文件夹: {current_folder_name}")
                print(f"  - {file}")


# 示例用法
if __name__ == "__main__":
    directory_path = "/Volumes/zhiwang"  # 替换为你要遍历的目录路径
    list_pdfs_in_directory(directory_path)
