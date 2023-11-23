# -*- coding: utf-8 -*-
import oss2
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


def encrypt(plain_text, key=bytes([95, 95, 103, 95, 95, 115, 116, 101, 97, 109, 95, 105, 110, 105, 116, 115])):
    cipher = AES.new(key, AES.MODE_ECB)
    padded_plain_text = pad(plain_text.encode(), AES.block_size)
    encrypted_data = cipher.encrypt(padded_plain_text)
    return encrypted_data.hex().upper()


def decrypt(cipher_text, key=bytes([95, 95, 103, 95, 95, 115, 116, 101, 97, 109, 95, 105, 110, 105, 116, 115])):
    encrypted_data = bytes.fromhex(cipher_text)
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted_data = cipher.decrypt(encrypted_data)
    unpadded_plain_text = unpad(decrypted_data, AES.block_size)
    return unpadded_plain_text.decode()



def upload_aliyun(dst_file, local_file):
    yourAccessKeyId = 'LTAI5tJG95GpSGr4jXeyu554'
    yourAccessKeySecret = 'pnz5ubi9Au4VSW7Psrfl1hhc0gXisQ'
    auth = oss2.Auth(yourAccessKeyId, yourAccessKeySecret)
    end_point = 'oss-cn-hangzhou.aliyuncs.com'
    bucket_name = 'laksdjflkajs'
    bucket = oss2.Bucket(auth, end_point, bucket_name)
    bucket.put_object_from_file(dst_file, local_file)

# 密钥
# key = bytes([95, 95, 103, 95, 95, 115, 116, 101, 97, 109, 95, 105, 110, 105, 116, 115])
# plaintext = '今天，我们聊聊相思，不知道各位心里会出现你的谁……默默想念一个人的滋味，只有心知道有一些人，这一辈子都不会在一起，但是有一种想念，却可以藏在心里一辈子。一曲相思苦，唱遍了多少人内心的惆怅，唱遍了多少人内心对那个人的思念。若不是因为爱着你，怎么会深夜还没睡意，每个念头都关于你。那一份思念的沉淀，那一份思念的心酸，或许只有自己能理解。默默想你，是我一个人爱的秘密。想你的时候不是因为我寂寞，而是我想你更寂寞。想念在心中，一种淡淡的滋味，幸福的滋味。想念的苦无人可知；想念的痛无人可懂，想念的滋味，只有心知道。我闭上眼睛，虽然看不见自己，但却可以看到你。爱如此简单，默默的关心，默默的想念。想你的时候，就算天涯海角，两颗心的距离却近在咫尺。有一个能够思念的人也是一种幸福。爱过你我足够了，待到白发苍苍时，再回想起那些美妙的时刻，何尝不是一种欣慰。有一种爱，不敢打扰，只能默默想念一生世间最苦的事情，就是思念一个人到了极致，却可以忍住不联系。有些人不是我不在意，只是我既不能相见，只适合在远方默默地牵挂与想念。有一种情它只添想，不添乱，彼此默默关怀，却互不打扰。我们心中都有那么一个特别的人，虽然有缘相遇，却无缘相守。爱不能联系，想念不能打扰，只能藏于心，留余情， 把我对你的爱化作思念。在没有你陪伴的日子里，我无数次有想要联系的冲动，几次拿起手机却又放下，因为爱你，所以不敢打扰。我会把我们最美的回忆留在我的心里，把你永远放在我心里，默默的思念，默默的祝福。别人说我看起来很洒脱，别人说我应该是忘了你，只有我自己清楚，心里有多想你。静夜，我也会静静地看着你亮着的头像，想着你，不去惊动，不去打扰。爱你，却有缘无分，只能默默思念你明明知道相思苦，偏偏对你苦相思。一个人，动了情，放不下；一段情，入了心，忘不了。有一种想念叫梦中见到了你，醒来你却不在身边，伸手却触摸不着，拥有的只是孤独寂寞的痛与忧伤。真爱一个人，再好的良药也治不了爱你的味道，再长的时间也磨灭不了爱一个人的心。有一种爱，有些爱，注定无法永恒，只能藏在心里，默默地想，默默的念，不想忘记，只想静静的回忆。世上真情难求，真爱难遇，好不容易遇见还彼此深爱，彼此懂得，却有缘无分。既然我们有缘无分，那么就一生思念，这是我最后的决定。人生最大的遗憾，莫过于遇见真爱，却无缘牵手。有一种爱，没在轰轰烈烈里，只能静悄悄在心里。默默地想念你，是我一个人的心事。默默地想念你，不会因为你不在身边而停止对你的思念。今夜我又为你失眠了，思念在蔓延，想你已是一种习惯……情到深处，才知思念的苦。相思蔓延，思念化不开，情意绕心头。很想把你从我的记忆中抹去，却总是身不由己地想起你：在梦中的每时每刻，在醒时的分分秒秒。最忧伤的爱情，莫过于，在错误的时间，却遇到了那个自己想要守护一生的人。如果有来生，我们一定要早点遇见，让我们三生三世，永生永世都不分离，好吗？（每个人心里都有一段刻骨的感情，不管如何请好好珍惜，因为此生能惊艳你时光的人真的不多，祝福天下有情人……） '
# encrypted_text = encrypt(plaintext)
# print('加密后数据:', encrypted_text)
#
# decrypted_text = decrypt(encrypted_text)
# print('解密后数据:', decrypted_text)
