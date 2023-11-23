import json


# 写入
def save_file(filename, content):
    # 将数据保存到文件中
    with open(f"config/{filename}", 'w', encoding='utf-8') as f:
        f.write(content)


# 读取
def load_file(filename):
    with open(f"config/{filename}", 'r', encoding='utf-8') as file:
        return json.load(file)
