"""
URL configuration for computeServer app.
"""
from django.contrib import admin
from django.urls import path

from network.server.computeServer import views

urlpatterns = [
    path('test/', views.test, name='test'),
    
    # Client API
    path('client/connect/', views.connect, name='connect'),
    path('client/pipeline/get/', views.get_pipeline, name='get_pipeline'),
    path('client/pipeline/new/', views.new_pipeline, name='new_pipeline'),
    path('client/pipeline/overwrite/', views.overwrite_pipeline, name='overwrite_pipeline'),
    path('client/pipeline/modifyparams/', views.modify_pipeline_params, name='modify_pipeline_params'),
    path('client/pipeline/run/', views.run_pipeline, name='run_pipeline'),
    path('client/pipeline/stop/', views.stop_pipeline, name='stop_pipeline'),
    path('client/pipeline/rerun/', views.rerun_pipeline, name='rerun_pipeline'),
    path('client/pipeline/getdownload/', views.get_download_uri, name='get_download_uri'),
    
    # Container API
    path('container/onstagecomplete/', views.on_stage_complete, name='on_stage_complete'),
    path('container/onpipelineerror/', views.on_pipeline_error, name='on_pipeline_error')
]
