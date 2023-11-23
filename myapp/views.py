from django.shortcuts import  render, redirect
import datetime
from .models import *
import os
import hashlib
import json
import requests
import json
import os
import datetime
from django.http import JsonResponse
def TaskView(request):
    context={}
    if request.method == "GET":
        return render(request, 'getpaper.html',context)
    elif request.method == "POST":
        context={}
        cmdstr=request.POST.get("cmdstr",'')
        print(cmdstr)

        qtasks=Task.objects.filter(keystr=cmdstr,flag=1)
        if len(qtasks)==0:
            task = Task()
            task.keystr = cmdstr

            task.flag=1
            task.save()
            os.system(cmdstr)
            context['json']='执行已执行成功'
            context['flag']=1
        else:
            oldtask=qtasks[0]
            now=datetime.datetime.now().strftime("%Y%m%d %H%M%S")
            delnow=str((datetime.datetime.now()+datetime.timedelta(minutes=-5)).strftime("%Y%m%d %H%M%S"))
            tasktime=str(oldtask.posttime.strftime("%Y%m%d %H%M%S"))
            print(now)
            print(delnow)
            print(tasktime)
            if tasktime>delnow:
                print('here')
                task = Task()
                task.keystr = cmdstr
                task.flag=0
                task.save()
                context['flag']=1
                context['json']='指令间隔时间过短，并未执行'
            else:
                oldtask.delete()
                task=Task()
                task.keystr=cmdstr
                task.flag=1
                task.save()
                os.system(cmdstr)
                context['json'] = '执行已执行成功'
                context['flag'] = 1

        return render(request, 'getpaper.html',context)
def TaskApi(request):
    context = {}
    if request.method == "POST":
        context['info'] = 'please use get request!'
        return JsonResponse(context, safe=True)
    elif request.method == "GET":
        context = {}
        cmdstr = request.GET.get("cmdstr", '')
        print(cmdstr)

        qtasks = Task.objects.filter(keystr=cmdstr, flag=1)
        if len(qtasks) == 0:
            task = Task()
            task.keystr = cmdstr
            task.flag = 1
            task.save()
            os.system(cmdstr)
            context['json'] = 'success'
            context['flag'] = 1
        else:
            oldtask = qtasks[0]
            now = datetime.datetime.now().strftime("%Y%m%d %H%M%S")
            delnow = str((datetime.datetime.now() + datetime.timedelta(minutes=-5)).strftime("%Y%m%d %H%M%S"))
            tasktime = str(oldtask.posttime.strftime("%Y%m%d %H%M%S"))
            print(now)
            print(delnow)
            print(tasktime)
            if tasktime > delnow:
                print('here')
                task = Task()
                task.keystr = cmdstr
                task.flag = 0
                task.save()
                context['flag'] = 1
                context['json'] = 'wait'
            else:
                oldtask.delete()
                task = Task()
                task.keystr = cmdstr
                task.flag = 1
                task.save()
                os.system(cmdstr)
                context['json'] = 'success'
                context['flag'] = 1

        return JsonResponse(context, safe=True)


def AddUserApi(request):
    context = {}
    if request.method == "POST":
        context['info'] = 'please use get request!'
        return JsonResponse(context, safe=True)
    elif request.method == "GET":
        try:
            context = {}
            cmdstr = request.GET.get("adduser", '')
            import json
            path = 'data/users.json'
            fr = open(path, 'r', encoding='utf-8')
            dt = json.load(fr)
            fr.close()
            print(dt)
            name = cmdstr.split('|')[0]
            mima = cmdstr.split('|')[1]
            if name in dt.keys():
                dt[name][0] = mima
                context['flag']='change mima sucess'
            else:
                dt[name] = [mima, None]
                context['flag'] = 'add user sucess'
            fw = open(path, 'w+', encoding='utf-8')
            fw.write(json.dumps(dt, ensure_ascii=False))
            fw.close()
            return JsonResponse(context, safe=True)
        except:
            context={}
            context['flag']='input error'
            return JsonResponse(context, safe=True)



def DelUserApi(request):
    context = {}
    if request.method == "POST":
        context['info'] = 'please use get request!'
        return JsonResponse(context, safe=True)
    elif request.method == "GET":
        try:
            context = {}
            cmdstr = request.GET.get("deluser", '')
            import json
            path = 'data/users.json'
            fr = open(path, 'r', encoding='utf-8')
            dt = json.load(fr)
            fr.close()
            print(dt)
            name = cmdstr

            if name in dt.keys():
                del dt[name]
                context['flag']='user delete sucess '
            else:

                context['flag'] = 'user not exist'
            fw = open(path, 'w+', encoding='utf-8')
            fw.write(json.dumps(dt, ensure_ascii=False))
            fw.close()
            return JsonResponse(context, safe=True)
        except:
            context={}
            context['flag']='input error'
            return JsonResponse(context, safe=True)