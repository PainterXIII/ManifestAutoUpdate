import json
import logging
import os
import subprocess
from threading import Thread

log = logging.getLogger('service')
dir_path = os.path.dirname(os.path.realpath(__file__))
user_info_path = os.path.join(dir_path, 'data/users.json')


# 查询用户信息,参数为用户名
def get_user_info(username):
    with open(user_info_path, 'r') as f:
        users = json.load(f)
        if username in users:
            data = {
                "code": 200,
                "msg": "用户信息查询成功",
                "username": username,
                "password": users[username][0]
            }
            return json.dumps(data, indent=4, separators=(',', ': '), ensure_ascii=False)
        else:
            data = {
                "code": 201,
                "msg": "用户不存在"
            }
            return json.dumps(data, indent=4, separators=(',', ': '), ensure_ascii=False)


# 删除用户信息,参数为列表
def delete_user_info(username_list):
    with open(user_info_path, 'r') as f:
        users = json.load(f)
        for username in username_list:
            if username in users:
                users.pop(username)
            else:
                log.info(f"{username}->用户不存在")
        with open(user_info_path, 'w') as f:
            json.dump(users, f, indent=4, separators=(',', ': '), ensure_ascii=False)
        data = {
            "code": 200,
            "msg": "用户信息删除成功"
        }
        return json.dumps(data, indent=4, separators=(',', ': '), ensure_ascii=False)


# 增加或修改用户信息,参数为json,如果已存在则修改密码,如果不存在,则增加
def add_user_info(user_info):
    with open(user_info_path, 'r') as f:
        users = json.load(f)
        for username in user_info:
            if username in users:
                users[username][0] = user_info[username]
            else:
                users[username] = [user_info[username], None]
        with open(user_info_path, 'w') as f:
            json.dump(users, f, indent=4, separators=(',', ': '), ensure_ascii=False)
        data = {
            "code": 200,
            "msg": "用户信息增加或修改成功"
        }
        return json.dumps(data, indent=4, separators=(',', ': '), ensure_ascii=False)


# 替换所有用户信息,参数为json
def replace_all_user_info(json_data):
    with open(user_info_path, 'w') as f:
        json.dump(json_data, f, indent=4, separators=(',', ': '), ensure_ascii=False)
    data = {
        "code": 200,
        "msg": "用户信息替换成功"
    }
    return json.dumps(data, indent=4, separators=(',', ': '), ensure_ascii=False)


"""
执行shell命令,参数为json
解析json后执行的命令为: python main.py -u -a app_id -U username
如果,传入的app_id的进程没有结束,则不执行重复的app_id的命令,需要写记录执行
进程结束后,从app_id_list中删除app_id
"""
shell_json = {
    "username": "wt6do7iu4ff1",
    "app_id": "1868140"
}

# 初始的 app_id_list
app_id_list = []

# 待执行的 app_id 列表
pending_app_id_list = []


# 解析 JSON 输入并执行命令
def execute_shell_command(shell_json):
    # 解析 JSON 字符串
    username = shell_json["username"]
    app_id = shell_json["app_id"]

    # 检测是否有进程在运行
    if app_id in app_id_list:
        log.info(f'App ID {app_id} is already running. Command will not be executed.')
        data = {
            "code": 201,
            "msg": f"当前{app_id}的进程正在运行,请等待进程结束后再执行命令"
        }
        return json.dumps(data, indent=4, separators=(',', ': '), ensure_ascii=False)

    # 检查 app_id_list 是否有空间，如果没有，则加入 pending_app_id_list
    if len(app_id_list) >= 5:
        pending_app_id_list.append(app_id)
        log.info(f'App ID {app_id} is added to pending list. Waiting for space to run.')
        data = {
            "code": 202,
            "msg": f"系统繁忙,您的{app_id}进程已加入等待队列"
        }
        return json.dumps(data, indent=4, separators=(',', ': '), ensure_ascii=False)
    else:
        # 在 app_id_list 中记录当前 app_id
        app_id_list.append(app_id)
        log.info(f'App ID {app_id} is added to running list.')

    # 启动新线程执行命令
    def run_command():
        try:
            command = f'python main.py -u -a {app_id} -U {username}'
            process = subprocess.Popen(command, shell=True)  # use shell=True to handle command as string
            log.info(f'Executing command: {command}')
            process.wait()  # 等待命令执行完成
            log.info(f'Command execution completed.')
        except Exception as e:
            print(f'An error occurred: {e}')
        finally:
            # 进程结束后应该删除 app_id
            if app_id in app_id_list:
                app_id_list.remove(app_id)
                log.info(f'App ID {app_id} is removed from running list.')
                # 如果存在待处理的app_id,启动一个
                if len(pending_app_id_list) > 0:
                    next_app_id = pending_app_id_list.pop(0)
                    log.info(f'App ID {next_app_id} is taken from pending list to run.')
                    shell_json["app_id"] = next_app_id
                    execute_shell_command(shell_json)  # 递归调用处理 next_app_id

    thread = Thread(target=run_command)
    thread.start()

    data = {
        "code": 200,
        "msg": f"{app_id} 进程已启动, Thanks!",
    }
    return json.dumps(data, indent=4, separators=(',', ': '), ensure_ascii=False)


# 初始的 app_id_list
# app_id_list = []
#
#
# # 解析 JSON 输入并执行命令
# def execute_shell_command(shell_json):
#     # 解析 JSON 字符串
#     # shell = json.loads(shell_json)
#     username = shell_json["username"]
#     app_id = shell_json["app_id"]
#
#     # 检测是否有进程在运行
#     if app_id in app_id_list:
#         log.info(f'App ID {app_id} is already running. Command will not be executed.')
#         data = {
#             "code": 201,
#             "msg": "当前app_id的进程正在运行,请等待进程结束后再执行命令"
#         }
#         return json.dumps(data, indent=4, separators=(',', ': '), ensure_ascii=False)
#
#     # 在 app_id_list 中记录当前 app_id
#     app_id_list.append(app_id)
#
#     # 启动新线程执行命令
#     def run_command():
#         try:
#             command = f'python main.py -u -a {app_id} -U {username}'
#             process = subprocess.Popen(command, shell=True)  # use shell=True to handle command as string
#             log.info(f'Executing command: {command}')
#             process.wait()  # 等待命令执行完成
#             log.info(f'Command execution completed.')
#         except Exception as e:
#             print(f'An error occurred: {e}')
#         finally:
#             # 进程结束后应该删除 app_id
#             if app_id in app_id_list:
#                 app_id_list.remove(app_id)
#
#     thread = Thread(target=run_command)
#     thread.start()
#
#     data = {
#         "code": 200,
#         "msg": f"{app_id} 进程已启动,Thanks!"
#     }
#     return json.dumps(data, indent=4, separators=(',', ': '), ensure_ascii=False)


if __name__ == '__main__':
    # post列表格式
    username_list = [
        "vlcq89982",
        "ojzo36629",
        "irq85580"
    ]

    user_info = {
        "ueru69941": "123456",
        "username1": "password1",
        "username2": "password2"
    }

    # 测试运行
    # process = execute_shell_command(shell_json=shell_json)

    # print(get_user_info('vlcq89982'))
    # print(delete_user_info(username_list))
    # print(add_user_info(user_info))
    # print(replace_all_user_info({"admin": ["1234567", None]}))
