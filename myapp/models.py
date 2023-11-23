from django.db import models

class Task(models.Model):
    keystr=models.CharField(verbose_name="指令", max_length=1000,blank=False)
    flag=models.IntegerField(verbose_name="是否运行", blank=False)
    posttime=models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = '任务管理'
        verbose_name_plural = verbose_name
    def __str__(self):
        return str(self.keystr)