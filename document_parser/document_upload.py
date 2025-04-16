import os


def save_to_tmp_dir(uploaded_files):
    # 定义临时文件夹名称
    TEMP_DIR = os.getenv("TMP_DIR")

    # 检查tmp目录是否存在
    if os.path.exists(TEMP_DIR):
        # 如果存在，清空tmp目录下的所有内容
        for root, dirs, files in os.walk(TEMP_DIR, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                os.remove(file_path)
            for name in dirs:
                dir_path = os.path.join(root, name)
                os.rmdir(dir_path)
    else:
        # 如果不存在，创建tmp目录
        os.makedirs(TEMP_DIR)

    file_list = []
    for file in uploaded_files:
        # 保存文件到tmp目录
        with open(os.path.join(TEMP_DIR, file.name), "wb") as f:
            f.write(file.getvalue())
        file_list.append(f"{TEMP_DIR}/{file.name}")
        

    print(f"files uploaded.\n{file_list}")
    return file_list