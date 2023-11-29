import os
import sys
import json
import time
import base64
import gevent
import logging

import functools
import traceback
from pathlib import Path
from steam.enums import EResult
from multiprocessing.pool import ThreadPool
from multiprocessing.dummy import Pool, Lock
from steam.guard import generate_twofactor_code
from DepotManifestGen.main import MySteamClient, MyCDNClient, get_manifest, BillingType
from steam.client.cdn import temp, CDNClient

lock = Lock()
sys.setrecursionlimit(100000)

dlc = {}
result_data = {}
new_result = {}
app_id_list = []


class MyJson(dict):

    def __init__(self, path):
        super().__init__()
        self.path = Path(path)
        self.load()

    def load(self):
        if not self.path.exists():
            self.dump()
            return
        with self.path.open() as f:
            self.update(json.load(f))

    def dump(self):
        with self.path.open('w') as f:
            json.dump(self, f)


class LogExceptions:
    def __init__(self, fun):
        self.__callable = fun
        return

    def __call__(self, *args, **kwargs):
        try:
            return self.__callable(*args, **kwargs)
        except KeyboardInterrupt:
            raise
        except:
            logging.error(traceback.format_exc())


class ManifestAutoUpdate:
    log = logging.getLogger('ManifestAutoUpdate')
    ROOT = Path('data').absolute()
    users_path = ROOT / Path('users.json')
    app_info_path = ROOT / Path('appinfo.json')
    user_info_path = ROOT / Path('userinfo.json')
    two_factor_path = ROOT / Path('2fa.json')
    app_lock = {}
    pool_num = 8
    retry_num = 3
    remote_head = {}
    update_wait_time = 86400
    tags = set()

    def __init__(self, credential_location=None, level=None, pool_num=None, retry_num=None, update_wait_time=None,
                 key=None, init_only=False, cli=False, app_id_list=None, user_list=None):

        if level:
            level = logging.getLevelName(level.upper())
        else:
            level = logging.INFO
        logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                            level=level)
        logging.getLogger('MySteamClient').setLevel(logging.WARNING)
        self.init_only = init_only
        self.cli = cli
        self.pool_num = pool_num or self.pool_num
        self.retry_num = retry_num or self.retry_num
        self.update_wait_time = update_wait_time or self.update_wait_time
        self.credential_location = Path(credential_location or self.ROOT / 'client')
        self.log.debug(f'credential_location: {credential_location}')
        self.key = key
        if not self.credential_location.exists():
            self.credential_location.mkdir(exist_ok=True)
        self.account_info = MyJson(self.users_path)
        self.user_info = MyJson(self.user_info_path)
        self.app_info = MyJson(self.app_info_path)
        self.two_factor = MyJson(self.two_factor_path)
        self.update_user_list = [*user_list] if user_list else []
        self.update_app_id_list = []
        if app_id_list:
            self.update_app_id_list = list(set(int(i) for i in app_id_list if i.isdecimal()))
            for user, info in self.user_info.items():
                if info['enable'] and info['app']:
                    for app_id in info['app']:
                        if app_id in self.update_app_id_list:
                            self.update_user_list.append(user)
        self.update_user_list = list(set(self.update_user_list))

    def get_manifest_callback(self, username, app_id, depot_id, manifest_gid, args):
        result = args.value
        if not result:
            self.log.warning(f'User {username}: get_manifest return {result.code.__repr__()}')
            return
        try:
            delete_list = result.get('delete_list') or []
            if len(delete_list) > 1:
                self.log.warning('Deleted multiple files?')
            self.set_depot_info(depot_id, manifest_gid)
        except KeyboardInterrupt:
            raise
        except:
            logging.error(traceback.format_exc())
        finally:
            with lock:
                if int(app_id) in self.app_lock:
                    self.app_lock[int(app_id)].remove(depot_id)
                    if int(app_id) not in self.user_info[username]['app']:
                        self.user_info[username]['app'].append(int(app_id))
                    if not self.app_lock[int(app_id)]:
                        self.log.debug(f'Unlock app: {app_id}')
                        self.app_lock.pop(int(app_id))

    def set_depot_info(self, depot_id, manifest_gid):
        with lock:
            self.app_info[depot_id] = manifest_gid

    def set_gid_info(self, depot_id, manifest_gid):
        with lock:
            self.app_info[depot_id]["manifest_gid"] = manifest_gid

    def save_user_info(self):
        with lock:
            self.user_info.dump()

    def save(self):
        self.save_depot_info()
        self.save_user_info()

    def save_depot_info(self):
        with lock:
            self.app_info.dump()

    def retry(self, fun, *args, retry_num=-1, **kwargs):
        while retry_num:
            try:
                return fun(*args, **kwargs)
            except gevent.timeout.Timeout as e:
                retry_num -= 1
                self.log.warning(e)
            except Exception as e:
                self.log.error(e)
                return

    def login(self, steam, username, password):
        self.log.info(f'Logging in to account {username}!')
        shared_secret = self.two_factor.get(username)
        steam.username = username
        result = steam.relogin()

        wait = 1
        if result != EResult.OK:
            if result != EResult.Fail:
                self.log.warning(f'User {username}: Relogin failure reason: {result.__repr__()}')
            if result in (EResult.RateLimitExceeded, EResult.AccountLoginDeniedThrottle):
                with lock:
                    time.sleep(wait)
            result = steam.login(username, password, steam.login_key, two_factor_code=generate_twofactor_code(
                base64.b64decode(shared_secret)) if shared_secret else None)
        count = self.retry_num
        while result != EResult.OK and count:
            if self.cli:
                with lock:
                    self.log.warning(f'Using the command line to interactively log in to account {username}!')
                    result = steam.cli_login(username, password)
                break
            elif result in (EResult.RateLimitExceeded, EResult.AccountLoginDeniedThrottle):
                if not count:
                    break
                with lock:
                    time.sleep(wait)
                result = steam.login(username, password, steam.login_key, two_factor_code=generate_twofactor_code(
                    base64.b64decode(shared_secret)) if shared_secret else None)
            elif result in (EResult.AccountLogonDenied, EResult.AccountDisabled,
                            EResult.AccountLoginDeniedNeedTwoFactor, EResult.PasswordUnset):
                logging.warning(f'User {username} has been disabled!')
                self.user_info[username]['enable'] = False
                self.user_info[username]['status'] = result
                break
            wait += 1
            count -= 1
            self.log.error(f'User {username}: Login failure reason: {result.__repr__()}')
        if result == EResult.OK:
            # print('friends set:',)
            self.log.info(f'User {username} login successfully!')
        else:
            self.log.error(f'User {username}: Login failure reason: {result.__repr__()}')
        return result

    def async_task(self, save_id, cdn, app_id, depot_id, manifest_gid):
        return get_manifest(save_id, cdn, app_id, depot_id, manifest_gid, True, self.ROOT, self.retry_num)

    def get_manifest(self, username, password, sentry_name=None):
        with lock:
            if username not in self.user_info:
                self.user_info[username] = {}
                self.user_info[username]['app'] = []
            if 'update' not in self.user_info[username]:
                self.user_info[username]['update'] = 0
            if 'enable' not in self.user_info[username]:
                self.user_info[username]['enable'] = True
            if not self.user_info[username]['enable']:
                logging.warning(f'User {username} is disabled!')
                return
        t = self.user_info[username]['update'] + self.update_wait_time - time.time()
        if t > 0:
            logging.warning(f'User {username} interval from next update: {int(t)}s!')
            return
        sentry_path = None
        if sentry_name:
            sentry_path = Path(
                self.credential_location if self.credential_location else MySteamClient.credential_location) / sentry_name
        self.log.debug(f'User {username} sentry_path: {sentry_path}')
        steam = MySteamClient(str(self.credential_location), sentry_path)
        result = self.login(steam, username, password)
        if result != EResult.OK:
            return
        self.log.info(f'User {username}: Waiting to initialize the cdn client!')
        cdn = self.retry(MyCDNClient, steam, retry_num=self.retry_num)
        if not cdn:
            logging.error(f'User {username}: Failed to initialize cdn!')
            return

        global app_id_list, new_dlc
        if cdn.packages_info:
            self.log.info(f'User {username}: Waiting to get packages info!')
            product_info = self.retry(steam.get_product_info, packages=cdn.packages_info, retry_num=self.retry_num)
            if not product_info:
                logging.error(f'User {username}: Failed to get packages info!')
                return
            if cdn.packages_info:
                for package_id, info in product_info['packages'].items():
                    if 'depotids' in info and info['depotids'] and info['billingtype'] in BillingType.PaidList:
                        app_id_list.extend(list(info['appids'].values()))
        self.log.info(f'User {username}: {len(app_id_list)} paid app found!')
        if not app_id_list:
            self.user_info[username]['enable'] = False
            self.user_info[username]['status'] = result
            logging.warning(f'User {username}: Does not have any app and has been disabled!')
            return
        self.log.debug(f'User {username}, paid app id list: ' + ','.join([str(i) for i in app_id_list]))
        self.log.info(f'User {username}: Waiting to get app info!')
        fresh_resp = self.retry(steam.get_product_info, app_id_list, retry_num=self.retry_num)

        #self.log.info(f"fresh_resp: {fresh_resp['apps']}")
        if not fresh_resp:
            logging.error(f'User {username}: Failed to get app info!')
            return
        job_list = []
        flag = True
        self.log.info(f"User {username}: {app_id_list}")

        for app_id in app_id_list:
            if int(app_id) not in self.update_app_id_list:
                continue
            with lock:
                if int(app_id) in self.app_lock:
                    continue
                self.log.debug(f'Lock app: {app_id}')
                self.app_lock[int(app_id)] = set()
                result_data[int(app_id)] = {}
                dlc[int(app_id)] = []
            try:
                app = fresh_resp['apps'][app_id]
            except:
                continue
            new_result.update(app)
            try:
                old_dlc = app['extended']["listofdlc"]
                if "," in old_dlc:
                    new_dlc = [int(i) for i in old_dlc.split(',')]
                    # 将列表写入到"dlc.txt"文件
                    dlc_file_path = f"data/depots/{app_id}/dlc.txt"

                    # 检查文件夹是否存在，如果不存在则创建
                    folder_path = os.path.dirname(dlc_file_path)
                    if not os.path.exists(folder_path):
                        os.makedirs(folder_path)

                    # 打开文件并写入数据
                    with open(dlc_file_path, "w") as f:
                        for item in new_dlc:
                            f.write(str(item) + "\n")
                    self.log.info(f"dlc_list: {fresh_resp['apps'].keys()}")
                    #dlc[int(app_id)].extend(new_dlc)
                    for i in fresh_resp['apps'].keys():
                        if fresh_resp['apps'][int(i)]['common']['type'] != 'Game':
                            dlc[int(app_id)].append(int(i))
                            CDNClient.temp_json["temp_dlc"].append(i)
                    #self.log.info(f"all_dlc_list: {new_dlc}")

                else:
                    dlc[int(app_id)].append(int(old_dlc))
                    self.log.info(f"old_dlc: {old_dlc}")
            except Exception as e:
                            traceback.print_exc()
            if 'common' in app and app['common']['type'].lower() in ['game', 'dlc', 'application']:
                if 'depots' not in fresh_resp['apps'][app_id]:
                    continue
                self.log.info(dlc)
                # 先处理原有的depots
                depots_to_process = fresh_resp['apps'][app_id]['depots']
                # 此处添加将DLC depots合并到处理流程的代码
                # 在这里，我们需要处理每个DLC的depots
                for key, values_list in dlc.items():
                    # 遍历与该键关联的值列表
                    for value in values_list:
                        #print(value)
                        try:
                            dlc_depots = fresh_resp['apps'][value]['depots']
                            if dlc_depots:
                                depots_to_process.update(dlc_depots)
                        except Exception as e:
                            # self.log.error(f"发生错误: {traceback.format_exc()}")
                            self.log.error(f"{value} 未能解析到depot_id & gid")
                            continue
                counter = 0  # 初始化计数器
                item = None  # 定义临时变量
                for depot_id, depot in depots_to_process.items():
                    #self.log.info(f"depot_id: {depot_id}")
                    with lock:
                        if depot_id.isdigit():
                            self.app_lock[int(app_id)].add(depot_id)
                            try:
                                if int(app_id) not in result_data:
                                    result_data[int(app_id)] = {}
                                if int(depot_id) not in result_data[int(app_id)]:
                                    result_data[int(app_id)][int(depot_id)] = set()
                            except KeyError:
                                self.log.error("Error adding depot_id to result_data")
                    if 'manifests' in depot and 'public' in depot['manifests'] and int(depot_id) in {
                        *cdn.licensed_depot_ids, *cdn.licensed_app_ids}:
                        try:
                            manifest_gid = depot['manifests']['public']
                        except KeyError:
                            self.log.error("No public manifest for this depot")
                            continue

                        if isinstance(manifest_gid, dict):
                            manifest_gid = manifest_gid.get('gid')
                        if not isinstance(manifest_gid, str):
                            continue

                        self.set_depot_info(depot_id, manifest_gid)
                        if manifest_gid not in result_data[int(app_id)][int(depot_id)]:
                            result_data[int(app_id)][int(depot_id)].add(manifest_gid)

                        with lock:
                            if int(app_id) not in self.user_info[username]['app']:
                                self.user_info[username]['app'].append(int(app_id))
                                self.log.info(f"Added new app_id: {app_id}")
                        flag = False
                        if counter == 0:
                            # 第一次循环
                            item = app_id
                        else:
                            # 其他次循环
                            item = int(depot_id)
                        # job = gevent.Greenlet(LogExceptions(self.async_task), cdn, app_id, depot_id, manifest_gid)
                        job = gevent.Greenlet(LogExceptions(self.async_task), app_id, cdn, item, depot_id, manifest_gid)
                        job.rawlink(
                            # functools.partial(self.get_manifest_callback, username, app_id, depot_id, manifest_gid))
                            functools.partial(self.get_manifest_callback, username, item, depot_id, manifest_gid))
                        job_list.append(job)
                        gevent.idle()
                        counter += 1

                for job in job_list:
                    job.start()
            with lock:
                if int(app_id) in self.app_lock and not self.app_lock[int(app_id)]:
                    self.log.debug(f'Unlock app: {app_id}')
                    self.app_lock.pop(int(app_id))
            # except:
            #     self.log.error("error")

        with lock:
            if flag:
                self.user_info[username]['update'] = int(time.time())
        gevent.joinall(job_list)

    def run(self, update=False):
        if not self.account_info or self.init_only:
            self.save()
            self.account_info.dump()
            return
        if update and not self.update_user_list:
            self.update()
            if not self.update_user_list:
                return
        with Pool(self.pool_num) as pool:
            pool: ThreadPool
            result_list = []
            for username in self.account_info:
                if self.update_user_list and username not in self.update_user_list:
                    self.log.debug(f'User {username} has skipped the update!')
                    continue
                password, sentry_name = self.account_info[username]
                result_list.append(
                    pool.apply_async(LogExceptions(self.get_manifest), (username, password, sentry_name)))
            try:
                while pool._state == 'RUN':
                    if all([result.ready() for result in result_list]):
                        self.log.info('The program is finished and will exit in 1 seconds!')
                        time.sleep(1)
                        break
                    self.save()
                    time.sleep(1)
            except KeyboardInterrupt:
                with lock:
                    pool.terminate()
                os._exit(0)
            finally:
                self.save()

    def update(self):
        app_id_list = []
        for user, info in self.user_info.items():
            if info['enable']:
                if info['app']:
                    app_id_list.extend(info['app'])
        app_id_list = list(set(app_id_list))
        logging.debug(app_id_list)
        steam = MySteamClient(str(self.credential_location))
        self.log.info('Logging in to anonymous!')
        steam.anonymous_login()
        self.log.info('Waiting to get all app info!')
        app_info_dict = {}
        count = 0
        while app_id_list[count:count + 300]:
            fresh_resp = self.retry(steam.get_product_info, app_id_list[count:count + 300],
                                    retry_num=self.retry_num, timeout=60)
            count += 300
            if fresh_resp:
                for app_id, info in fresh_resp['apps'].items():
                    if depots := info.get('depots'):
                        app_info_dict[int(app_id)] = depots
                self.log.info(f'Acquired {len(app_info_dict)} app info!')
        update_app_set = set()
        for app_id, app_info in app_info_dict.items():
            for depot_id, depot in app_info.items():
                if depot_id.isdecimal():
                    if manifests := depot.get('manifests'):
                        if manifest := manifests.get('public'):
                            if depot_id in self.app_info and self.app_info[depot_id] != manifest:
                                update_app_set.add(app_id)
        update_app_user = {}
        update_user_set = set()
        for user, info in self.user_info.items():
            if info['enable'] and info['app']:
                for app_id in info['app']:
                    if int(app_id) in update_app_set:
                        if int(app_id) not in update_app_user:
                            update_app_user[int(app_id)] = []
                        update_app_user[int(app_id)].append(user)
                        update_user_set.add(user)
        self.log.debug(str(update_app_user))
        for user in self.account_info:
            if user not in self.user_info:
                update_user_set.add(user)
        self.update_user_list.extend(list(update_user_set))
        for app_id, user_list in update_app_user.items():
            self.log.info(f'{app_id}: {",".join(user_list)}')
        self.log.info(f'{len(update_app_user)} app and {len(self.update_user_list)} users need to update!')
        return self.update_user_list
