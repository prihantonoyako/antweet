from django.urls import path
from preprocessing import views

urlpatterns = [
    path('ibukota-baru', views.pre_process)
]