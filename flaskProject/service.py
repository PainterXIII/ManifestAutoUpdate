import json
import logging
import os

log = logging.getLogger('service')
dir_path = os.path.dirname(os.path.realpath(__file__))
user_info_path = os.path.join(dir_path, '../data/users.json')


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
    # print(get_user_info('vlcq89982'))
    # print(delete_user_info(username_list))
    # print(add_user_info(user_info))
    # print(replace_all_user_info({"admin": ["1234567", None]}))
