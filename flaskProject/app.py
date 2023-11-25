from flask import Flask, request
from service import *

app = Flask(__name__)


# 查询用户信息
@app.route('/get_user')
def get_user():
    # 获取get参数中的username
    username = request.args.get('username')
    # 调用service.py中的get_user_info方法
    return get_user_info(username), {'Content-Type': 'text/json; charset=utf-8'}


"""
    user_info = {
        "ueru69941": "123456",
        "username1": "password1",
        "username2": "password2"
    }
"""


# 增加或修改用户信息,参数为json,协议POST
@app.route('/add_user', methods=['POST'])
def add_user():
    # 获取post参数中的user_info
    user_info = request.get_json()
    # 调用service.py中的add_user_info方法
    return add_user_info(user_info), {'Content-Type': 'text/json; charset=utf-8'}


"""
username_list = [
        "vlcq89982",
        "ojzo36629",
        "irq85580"
    ]
"""


# 删除用户信息,参数为列表,协议POST
@app.route('/delete_user', methods=['POST'])
def delete_user():
    # 获取post参数中的username_list
    username_list = request.get_json()
    # 调用service.py中的delete_user_info方法
    return delete_user_info(username_list), {'Content-Type': 'text/json; charset=utf-8'}


# 替换所有用户信息,参数为json,协议POST
@app.route('/replace_all_user', methods=['POST'])
def replace_all_user():
    # 获取post参数中的json_data
    json_data = request.get_json()
    # 调用service.py中的replace_all_user_info方法
    return replace_all_user_info(json_data), {'Content-Type': 'text/json; charset=utf-8'}


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
