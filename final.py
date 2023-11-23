# 读取new_fresh.json
import json
import os
import re

if __name__ == '__main__':
    app_id = "1902690"
    # 如果new_fresh.json存在,则打开读取
    if os.path.exists('new_fresh.json'):
        fr = open('new_fresh.json', 'r', encoding='utf-8')
        json_data = json.loads(fr.read())
        #print(json_data)
        # 创建app_id.txt并追加数据
        fw = open(app_id + '.txt', 'a+', encoding='utf-8')
        fw.write(f"{json_data[app_id]['iuser']}\n")
        # 如果data/depots/{app_id}/config.vdf存在,则打开,转为json格式,并追加数据
        if os.path.exists(f"data/depots/{app_id}/config.vdf"):
            fr = open(f"data/depots/{app_id}/config.vdf", 'r', encoding='utf-8')
            # 定义一个正则表达式模式
            pattern = r'"(\d+)"\s+{\s+"DecryptionKey"\s+"([\da-f]+)"\s+}'
            # 在 VDF 数据中查找匹配的键值对
            matches = re.findall(pattern, fr.read())
            # 将匹配的结果存储在字典中
            results = {}
            for match in matches:
                app_id = match[0]
                decryption_key = match[1]
                results[app_id] = decryption_key
                fw.write(f"{app_id}----{decryption_key}\n")
            # 打印结果
            #print(results)
            # 结尾添加 ticket
            # 解析 JSON 数据
            # 提取 "ticket" 值
            tickets = {}
            for app_id, app_data in json_data.items():
                if isinstance(app_data, dict) and "ticket" in app_data:
                    ticket = app_data["ticket"]
                    tickets[app_id] = ticket
                    fw.write(f"{tickets[app_id]}\n")



