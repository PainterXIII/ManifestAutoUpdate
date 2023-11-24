import json
import logging
import os
import re

from reptile import parser, ManifestAutoUpdate, result_data, dlc
from steam.utils.tools import upload_aliyun

log = logging.getLogger('ManifestAutoUpdate')

def end(app_id):
        end_id = app_id
        temp_path = f"data/depots/temp.json"
        if os.path.exists(temp_path):
            fr = open(temp_path, 'r', encoding='utf-8')
            json_data = json.loads(fr.read())
            # print(json_data)
            # 创建app_id.txt并追加数据
            result_path = f"data/depots/{app_id}/{app_id}.txt"
            fw = open(result_path, 'a+', encoding='utf-8')
            for _iuser in json_data['iuser']:
                fw.write(f"{_iuser}\n")
            # 如果data/depots/{app_id}/config.vdf存在,则打开,转为json格式,并追加数据
            """
            这块代码是为了获取config.vdf中的DecryptionKey
            """
            config_path = f"data/depots/{app_id}/config.vdf"
            if os.path.exists(config_path):
                fr = open(config_path, 'r', encoding='utf-8')
                # 定义一个正则表达式模式
                pattern = r'"(\d+)"\s+{\s+"DecryptionKey"\s+"([\da-f]+)"\s+}'
                # 在 VDF 数据中查找匹配的键值对
                matches = re.findall(pattern, fr.read())

                for match in matches:
                    app_id = match[0]
                    decryption_key = match[1]
                    fw.write(f"{app_id}----{decryption_key}\n")
                # 结尾添加 ticket
                # 结尾添加 ticket
                for ticket in json_data["ticket"]:
                    fw.write(f"{ticket}\n")
                log.info(f"END {app_id}.txt written successfully")
                fw.flush()
                fw.close()
                # 开始将data 字典中的 dlc 和 manifest_gid_list 写入到app_id_cache.txt中
                #log.info(f"dep_gid_data: {dep_gid_data}")
                app_id_cache_path = f"data/depots/{end_id}/{end_id}_cache.txt"
                fc = open(app_id_cache_path, 'a+', encoding='utf-8')
                # 遍历目录下的文件和子目录
                for root, dirs, files in os.walk(f"data/depots/{end_id}"):
                    for file in files:
                        # 检查文件后缀名是否为 .manifest
                        if file.endswith(".manifest"):
                            upload_aliyun(f"depotcache/{end_id}/{file}", f"data/depots/{end_id}/{file}")
                            log.info(f"Done,{file} upload success")
                            fc.write(file.replace(".manifest", "") + "\n")
                # 继续遍历
                
                fc.flush()
                fc.close()
                log.info(f"END {app_id}_cache.txt written successfully")
                try:
                    upload_aliyun(f"gKeyConfig/{end_id}.txt", result_path)
                    upload_aliyun(f"depotcache/{end_id}/{end_id}.txt", app_id_cache_path)
                    log.info(f"Done,data uploaded successfully")
                except Exception as e:
                    log.error(f"Completed,{app_id}_cache.txt upload failed. Error: {str(e)}")

                # 清理临时文件
                os.remove(temp_path)
                os.remove(app_id_cache_path)
if __name__ == '__main__':
    args = parser.parse_args()
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
    end(args.app_id_list[0])