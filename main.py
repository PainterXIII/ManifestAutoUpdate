import json
import logging
import os
import re
import argparse
from reptile import ManifestAutoUpdate, result_data, dlc
from steam.utils.tools import upload_aliyun, encrypt
from steam.client.cdn import temp, CDNClient

def delete_files(folder_path):
    if os.path.exists(folder_path):  # 检查文件夹是否存在
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file != 'dlc.txt':  # 指定要保留的文件名，其他文件将被删除
                    file_path = os.path.join(root, file)
                    os.remove(file_path)
        log.info(f"{folder_path} 删除成功")
    else:
        log.info(f"{folder_path} 不存在,开始爬取")


def write_to_file(file_path, content, mode='a+', encoding='utf-8'):
    existing_lines = set()
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding=encoding) as fr:
            existing_lines = set(line.strip().replace('\r', '') for line in fr.readlines())

    with open(file_path, mode, encoding=encoding) as fw:
        for line in content:
            if line.strip() not in existing_lines:
                fw.write(f"{line}\n")


def write_to_ticket(file_path, content, mode='a+', encoding='utf-8'):
    with open(file_path, mode, encoding=encoding) as fw:
        fw.write(f"{content}\n")


def read_vdf_config(config_path, pattern=r'"(\d+)"\s+{\s+"DecryptionKey"\s+"([\da-f]+)"\s+}'):
    if not os.path.exists(config_path):
        return []

    with open(config_path, 'r', encoding='utf-8') as fr:
        return re.findall(pattern, fr.read())


def upload_file(local_path, remote_path):
    try:
        upload_aliyun(remote_path, local_path)
        log.info(f"Upload successful: {local_path}")
    except Exception as e:
        log.error(f"Upload failed for {local_path}. Error: {str(e)}")


def cleanup_temp_files(files):
    for file in files:
        os.remove(file)
        log.info(f"Temporary file removed: {file}")


def end(app_id, json_data):
    if json_data is None:
        return

    result_path = f"data/depots/{app_id}/{app_id}.txt"
    config_path = f"data/depots/{app_id}/config.vdf"
    app_id_cache_path = f"data/depots/{app_id}/{app_id}_cache.txt"

    # 将数据写入app_id.txt
    write_to_file(result_path, json_data['iuser'])

    matches = read_vdf_config(config_path)
    if matches:
        write_to_file(result_path, [f"{match[0]}----{match[1]}" for match in matches])

    # 创建一个空列表用于存储不在matches和ticket_dict中的值
    temp_dlc_values = []
    # 判断data/depots/dlc.txt是否存在,存在则读取内容添加到json_data["temp_dlc"]
    if os.path.exists(f"data/depots/{app_id}/dlc.txt"):
        with open(f"data/depots/{app_id}/dlc.txt", 'r', encoding='utf-8') as f:
            for line in f.readlines():
                json_data["temp_dlc"].append(line.strip())
    for ticket_dict in json_data["ticket"]:
        # 遍历字典中的每个键值对
        for key, value in ticket_dict.items():
            # 判断值是否既不在matches中也不在ticket_dict中
            # 遍历temp_dlc列表内的值
            for dlc in json_data["temp_dlc"]:
                if str(dlc) not in [match[0] for match in matches] and str(dlc) not in key:
                    if str(dlc) not in temp_dlc_values:
                        temp_dlc_values.append(str(dlc))

    if temp_dlc_values is not None:
        for dlc in temp_dlc_values:
            # 将匹配结果和temp_dlc_values写入文件
            write_to_ticket(result_path, dlc)
    for ticket_dict in json_data["ticket"]:
        # 遍历字典中的每个键值对
        for key, value in ticket_dict.items():
            write_to_ticket(result_path, encrypt(key + '----' + value))

    logging.info(f"{app_id}.txt written successfully")

    # 写入app_id_cache.txt并上传文件
    with open(app_id_cache_path, 'a+', encoding='utf-8') as fc:
        for root, dirs, files in os.walk(f"data/depots/{app_id}"):
            for file in files:
                if file.endswith(".manifest"):
                    manifest_path = os.path.join(root, file)
                    upload_file(manifest_path, f"depotcache/{app_id}/{file}")
                    fc.write(file.replace(".manifest", "") + "\n")

    logging.info(f"{app_id}_cache.txt written successfully")

    # 上传结果文件
    if os.path.exists(result_path):
        upload_file(result_path, f"gKeyConfig/{app_id}.txt")

    if os.path.exists(app_id_cache_path):
        upload_file(app_id_cache_path, f"depotcache/{app_id}/{app_id}.txt")
        cleanup_temp_files([app_id_cache_path])
    # upload_file(result_path, f"gKeyConfig/{app_id}.txt")
    # upload_file(app_id_cache_path, f"depotcache/{app_id}/{app_id}.txt")
    # # 清理临时文件
    # cleanup_temp_files([app_id_cache_path])


# 初始化日志记录器
log = logging.getLogger('ManifestAutoUpdate')

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--credential-location', default=None)
    parser.add_argument('-l', '--level', default='INFO')
    parser.add_argument('-p', '--pool-num', type=int, default=8)
    parser.add_argument('-r', '--retry-num', type=int, default=3)
    parser.add_argument('-t', '--update-wait-time', type=int, default=86400)
    parser.add_argument('-k', '--key', default=None)
    parser.add_argument('-x', '--x', default=None)
    parser.add_argument('-i', '--init-only', action='store_true', default=False)
    parser.add_argument('-C', '--cli', action='store_true', default=False)
    parser.add_argument('-P', '--no-push', action='store_true', default=False)
    parser.add_argument('-u', '--update', action='store_true', default=False)
    parser.add_argument('-a', '--app-id', dest='app_id_list', action='extend', nargs='*')
    parser.add_argument('-U', '--users', dest='user_list', action='extend', nargs='*')
    args = parser.parse_args()
    temp["temp_id"].append(args.app_id_list[0])  # 将app_id赋给cdn.py
    log.info(args)
    ManifestAutoUpdate(args.credential_location, level=args.level, pool_num=args.pool_num, retry_num=args.retry_num,
                       update_wait_time=args.update_wait_time, key=args.key, init_only=args.init_only,
                       cli=args.cli, app_id_list=args.app_id_list, user_list=args.user_list).run(update=args.update)
    format_url_list = [
        "https://gh-proxy.com/https://raw.githubusercontent.com/heyong5454/ManifestAutoUpdate/{sha}/{path}",
        "https://github.moeyy.xyz/https://raw.githubusercontent.com/heyong5454/ManifestAutoUpdate/{sha}/{path}",
        "https://ghproxy.com/https://raw.githubusercontent.com/heyong5454/ManifestAutoUpdate/{sha}/{path}",
        "https://hub.fgit.ml/heyong5454/ManifestAutoUpdate/raw/{sha}/{path}",
        "https://hub.yzuu.cf/heyong5454/ManifestAutoUpdate/raw/{sha}/{path}",
        "https://raw.kgithub.com/heyong5454/ManifestAutoUpdate/{sha}/{path}",
        "https://hub.nuaa.cf/heyong5454/ManifestAutoUpdate/raw/{sha}/{path}"
    ]
    data = {}
    for _app_id in result_data:
        depot_id_list = []
        manifest_gid_list = []
        data[_app_id] = {
            "app_id": _app_id,
            "depot_id_list": [],
            "dlc": [],
            "format_url_list": format_url_list,
            "manifest_gid_list": [],
            "show": True
        }

        for depot_id, gid_set in result_data[_app_id].items():
            for gid in gid_set:
                depot_id_list.append(depot_id)
                manifest_gid_list.append(gid)
        data[_app_id]["depot_id_list"] = depot_id_list
        data[_app_id]["manifest_gid_list"] = manifest_gid_list

        log.info(f"manifest_gid_list: {manifest_gid_list}")
        if _app_id in dlc:
            data[_app_id]["dlc"] = dlc[_app_id]
    log.info(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))

    # 爬虫进程结束,开始处理数据
    end(args.app_id_list[0], CDNClient.temp_json)
    # log.info(CDNClient.temp_json)