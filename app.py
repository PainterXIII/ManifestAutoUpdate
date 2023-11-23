"""
shell_code
author: PainterXIII
"""
import json
import os
import subprocess

from flask import Flask, request, render_template
from tools import save_file, load_file

app = Flask("app")


def execute_shell_command(command):
    # 使用subprocess.Popen执行Shell命令，并将标准输出流设置为PIPE
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True)
    # 实时获取输出并打印
    for line in process.stdout:
        print(line, end='')


def test(args):
    for i in range(0, 1000000):
        print(i)


def get_filedate(filename):
    # 配置文件路径
    config_path = "config"
    file_path = os.path.join(config_path, f"{filename}.json")
    # 获取文件修改时间
    try:
        file_modified_time = os.path.getmtime(file_path)
    except FileNotFoundError:
        print("文件不存在！")
        return -3
    else:
        json = load_file(f"{filename}.json")
        if json["code"] == -1:
            print("数据正在处理中，请勿重复提交")
            return -1
        if json["code"] == -2:
            print("数据正在上传中，请勿重复提交")
            return -2
        elif json["code"] == 200:
            print("数据更新完成，请稍后重试游戏")
            return 200
        elif json["code"] == -4:
            print("更新限制,请联系客服")
            return -4
        elif json["code"] == -5:
            print("更新失败,请联系客服")
            return -5
        else:
            return -3


import threading


@app.route('/shellcode', methods=["POST", "GET"])
def shell_code():
    postall = str(request.stream.read(), encoding='utf-8')
    result = json.loads(postall)
    print(result)
    code = result["code"]
    appid = result["appid"]
    if get_filedate(appid) == -1:
        msg = "数据正在处理中，请勿重复提交"
        data = json.dumps({
            "code": -1,
            "msg": msg,
            "appid": appid
        }, indent=4, separators=(',', ': '), ensure_ascii=False)
        return data, {'Content-Type': 'text/json; charset=utf-8'}
    elif get_filedate(appid) == -2:
        msg = "数据正在上传中,请勿重复提交"
        data = json.dumps({
            "code": -2,
            "msg": msg,
            "appid": appid
        }, indent=4, separators=(',', ': '), ensure_ascii=False)
        return data, {'Content-Type': 'text/json; charset=utf-8'}
    elif get_filedate(appid) == 200:
        msg = "数据更新完成,请稍后重试游戏"
        data = json.dumps({
            "code": 200,
            "msg": msg,
            "appid": appid
        }, indent=4, separators=(',', ': '), ensure_ascii=False)
        return data, {'Content-Type': 'text/json; charset=utf-8'}
    elif get_filedate(appid) == -3:
        msg = "数据正在处理中,感谢使用"
        data = json.dumps({
            "code": -1,
            "msg": msg,
            "appid": appid
        }, indent=4, separators=(',', ': '), ensure_ascii=False)
        save_file(f"{appid}.json", data)
        # 创建一个新的线程，并将其设置为守护线程
        my_thread = threading.Thread(target=execute_shell_command, args=(code,), daemon=True)
        # 启动线程
        my_thread.start()
        return data, {'Content-Type': 'text/json; charset=utf-8'}
    elif get_filedate(appid) == -4:
        msg = "更新限制,请联系客服..."
        data = json.dumps({
            "code": -4,
            "msg": msg,
            "appid": appid
        }, indent=4, separators=(',', ': '), ensure_ascii=False)
        return data, {'Content-Type': 'text/json; charset=utf-8'}
    elif get_filedate(appid) == -5:
        msg = "更新失败,请联系客服..."
        data = json.dumps({
            "code": -5,
            "msg": msg,
            "appid": appid
        }, indent=4, separators=(',', ': '), ensure_ascii=False)
        return data, {'Content-Type': 'text/json; charset=utf-8'}


@app.route('/<path:path>')
def state(path):
    return load_file(f"{path}.json"), {'Content-Type': 'text/json; charset=utf-8'}


@app.route('/add', methods=["POST"])
def add():
    postall = str(request.stream.read(), encoding='utf-8')
    result = json.loads(postall)
    print(result)
    username = result['username']
    password = result['password']
    # 读取已有的JSON文件内容
    with open("data/users.json", "r") as file:
        existing_data = json.load(file)
    # 检查用户名是否存在
    if username in existing_data:
        # 更新密码
        existing_data[username][0] = password
        # 创建新的JSON数据
        new_data = {
            username: [
                password,
                None
            ]
        }
    else:
        # 创建新的JSON数据
        new_data = {
            username: [
                password,
                None
            ]
        }

        # 将新的JSON数据添加到特定字段中
        existing_data.update(new_data)

    # 将更新后的JSON数据重新转换为字符串
    json_str = json.dumps(existing_data)

    # 将新的JSON字符串写入文件
    with open("data/users.json", "w") as file:
        file.write(json_str)

    # 关闭文件
    file.close()
    return new_data, {'Content-Type': 'text/json; charset=utf-8'}


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)
