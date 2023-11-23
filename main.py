import json
import logging
import os
import re

from reptile import parser, ManifestAutoUpdate, result_data, dlc
from steam.utils.tools import upload_aliyun

log = logging.getLogger('ManifestAutoUpdate')
if __name__ == '__main__':
    def end(app_id, dep_gid_data):
        end_id = app_id
        temp_path = f"data/depots/temp.json"
        if os.path.exists(temp_path):
            fr = open(temp_path, 'r', encoding='utf-8')
            json_data = json.loads(fr.read())
            # print(json_data)
            # 创建app_id.txt并追加数据
            result_path = f"data/depots/{app_id}/{app_id}.txt"
            fw = open(result_path, 'a+', encoding='utf-8')
            fw.write(f"{json_data[app_id]['iuser']}\n")
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
                tickets = {}
                for app_id, app_data in json_data.items():
                    if isinstance(app_data, dict) and "ticket" in app_data:
                        ticket = app_data["ticket"]
                        tickets[app_id] = ticket
                        fw.write(f"{tickets[app_id]}\n")
                log.info(f"END {app_id}.txt 数据写入成功")
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
                fc.flush()
                fc.close()
                log.info(f"END {app_id}_cache.txt 数据写入成功")
                try:
                    upload_aliyun(f"gKeyConfig/{end_id}.txt", result_path)
                    upload_aliyun(f"depotcache/{end_id}/{end_id}.txt", app_id_cache_path)
                    log.info(f"Done,data uploaded successfully")
                except Exception as e:
                    log.error(f"Completed,{app_id}_cache.txt upload failed. Error: {str(e)}")




                # 清理临时文件
                #os.remove(temp_path)
                #os.remove(app_id_cache_path)


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
        # path = 'data/depots' + '/' + str(_app_id)
        # filepath = path + '/' + str(_app_id) + '-ticket.txt'
        # app_path = 'data/depots' + '/' + str(_app_id) + '/'
        #
        # if os.path.exists(filepath) and os.path.exists(app_path + 'addconfig.vdf'):
        #     log.info("上次已爬取")
        # else:
        #     fw = open(filepath, 'w+', encoding='utf-8')
        #     fw.close()
        #     log.info("无")
        # filepathonly = path + '/' + str(_app_id) + '-ticket-only.txt'
        # if os.path.exists(filepathonly) and os.path.exists(app_path + 'addconfig.vdf'):
        #     print('')
        # else:
        #     fw = open(filepathonly, 'w+', encoding='utf-8')
        #     fw.close()
        #     log.info("无")

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
    end(args.app_id_list[0], data)

    # if args.app_id_list != "":
    #     for app_id in args.app_id_list:
    #         path = 'data/depots' + '/' + str(app_id)
    #         filepath = path + '/' + str(app_id) + '-ticket.txt'
    #         app_path = 'data/depots' + '/' + str(app_id) + '/'
    #         try:
    #             fw = open(filepath, 'w+', encoding='utf-8')
    #             fw.close()
    #             filepathonly = path + '/' + str(app_id) + '-ticket-only.txt'
    #             fw = open(filepathonly, 'w+', encoding='utf-8')
    #             fw.close()
    #         except:
    #             log.info('error')
    #
    #         app_path = 'data/depots' + '/' + str(app_id) + '/'
    #
    #         addconfig = {}
    #         if os.path.exists(app_path + 'config.vdf'):
    #             d = vdf.load(open(app_path + 'config.vdf'))
    #         insert_appid(f"data/depots/", str(app_id))
    #         if os.path.exists(app_path + 'addconfig.vdf'):
    #             print('***************************---addconfig')
    #             adc = vdf.load(open(app_path + 'addconfig.vdf'))
    #             addconfig = adc['depots']
    #
    #             for key in addconfig.keys():
    #                 d['depots'][key] = addconfig[key]
    #
    #             with open(app_path + 'config.vdf', 'w') as f:
    #                 vdf.dump(d, f, pretty=True)
    #
    #
    #         def getDecryptionKey(path):
    #             fr = open(path, 'r', encoding='utf-8')
    #             lines = fr.readlines()
    #             totals = []
    #             i = 0
    #             while i < len(lines):
    #                 if lines[i].count('DecryptionKey') == 0:
    #                     i = i + 1
    #                     continue
    #                 key = lines[i - 2].strip().replace('"', '')
    #                 value = lines[i].split('"')[-2]
    #                 totals.append(key + '----' + value)
    #
    #                 i = i + 1
    #             return totals
    #
    #
    #         def jiami(code):
    #             url = 'http://47.98.52.241:8081/encryption'
    #             res = requests.post(url, code)
    #             return res.text
    #
    #
    #         dkeys = getDecryptionKey(app_path + 'config.vdf')
    #
    #         # os.remove(path + '/'+str(app_id) + '-ticket'+ '.txt')
    #         filepath = path + '/' + str(app_id) + '.txt'
    #         fr = open(filepath, 'r', encoding='utf-8')
    #         apptxts = fr.readlines()
    #         fr.close()
    #         fw = open(filepath, 'w+', encoding='utf-8')
    #         fw.write(apptxts[0].strip() + '\n')
    #         for item in dkeys:
    #             fw.write(item + '\n')
    #         for item in apptxts[1:]:
    #             fw.write(item.strip() + '\n')
    #
    #         fw.close()
    #         fr = open(filepath, 'r', encoding='utf-8')
    #         tlines = fr.readlines()
    #         fr.close()
    #         tls = []
    #         fw = open(filepath, 'w+', encoding='utf-8')
    #         for line in tlines:
    #             if line not in tls:
    #                 fw.write(line)
    #                 tls.append(line)
    #         fw.close()
    #
    #         def upload_aliyun(dst_file, local_file):
    #             import oss2
    #             yourAccessKeyId = 'LTAI5tJG95GpSGr4jXeyu554'
    #             yourAccessKeySecret = 'pnz5ubi9Au4VSW7Psrfl1hhc0gXisQ'
    #             auth = oss2.Auth(yourAccessKeyId, yourAccessKeySecret)
    #             end_point = 'oss-cn-hangzhou.aliyuncs.com'
    #             bucket_name = 'laksdjflkajs'
    #             bucket = oss2.Bucket(auth, end_point, bucket_name)
    #             bucket.put_object_from_file(dst_file, local_file)
    #             return True
    #
    #
    #         upload_aliyun('gKeyConfig/' + str(app_id) + '.txt', filepath)
    #
    #         files = os.listdir(path)
    #         fw = open('temp.txt', 'w+', encoding='utf-8')
    #
    #         for file in files:
    #             if file.endswith('fest') or file.endswith('svd'):
    #                 fw.write(file.split('.')[0] + '\n')
    #                 upload_aliyun('depotcache/' + str(app_id) + '/' + file, path + '/' + file)
    #
    #         fw.close()
    #         upload_aliyun('depotcache/' + str(app_id) + '/' + str(app_id) + '.txt', 'temp.txt')
    #         print('final      上传成功！')
