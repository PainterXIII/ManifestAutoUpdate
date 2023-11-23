# 遍历data/depots/1868140下的文件找到后缀名为manifest的文件

import os
from steam.utils.tools import upload_aliyun

end_id = "1868140"
app_id_cache_path = f"data/depots/{end_id}/{end_id}_cache.txt"
fc = open(app_id_cache_path, 'a+', encoding='utf-8')
directory = f"data/depots/{end_id}"
manifest_files = []

# 遍历目录下的文件和子目录
for root, dirs, files in os.walk(directory):
    for file in files:
        # 检查文件后缀名是否为 .manifest
        if file.endswith(".manifest"):
            manifest_files.append(os.path.join(root, file))
            # upload_aliyun("depotcache/appid/", os.path.join(root, file))
            fc.write(file.replace(".manifest", "") + "\n")
