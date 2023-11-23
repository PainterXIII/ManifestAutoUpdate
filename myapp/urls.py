from django.urls import path
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView,LogoutView

from . import views
#控制页面url路径
app_name = 'myapp'
urlpatterns = [
    path('index/', login_required(views.TaskView), name='index'),
    path('getpaper/', login_required(views.TaskView), name='getpaper'),
    path('task_api/', views.TaskApi, name='task_api'),
    path('adduser/', views.AddUserApi, name='adduser'),
    path('deluser/', views.DelUserApi, name='deluser'),
]