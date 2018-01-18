"""btc_cacheserver URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from btc_cacheserver.contract.views import update_load_data, \
    update_repayment_data, get_user_data
from btc_cacheserver.blockchain.views import get_block_detail_info, \
    get_transaction_detail_info, get_blocknumber_recording

urlpatterns = [
    path('admin/', admin.site.urls),
    path('bc/loan/update/', update_load_data),
    path('bc/repayment/update/', update_repayment_data),
    path('bc/query/', get_user_data),
    re_path('chain/block/(?P<number>\d+)/', get_block_detail_info),
    re_path('chain/tx/(?P<txhash>[A-Za-z0-9]+)/', get_transaction_detail_info),
    path('chain/blocknumber/', get_blocknumber_recording),
]
