from django.shortcuts import render
from monitor.models.bitasset.BitAssetAPI import BitAssetMarketAPI,BitAssetDealsAPI
import json
# from monitor.models.rountine_for_views import get_update_data
from django.http import JsonResponse
from monitor.models.bitasset.BitAssetInterface import *
from monitor.models.bitasset.bitasset_util import BitAsset
from datetime import timedelta
from monitor.models.tool import *
from monitor.models.rountine_for_views import Rountine
from monitor.models.dbOperation.UserInfo_Conf import UserName_UserId_dict
from  django.http import HttpResponse
from configparser import ConfigParser
# Create your views here.

symbolPair_contractId_dict={'ETH/BTC':10,'BCH/BTC':11,'LTC/BTC':12}
contractId_symbolPair_dict={10:'ETH/BTC',11:'BCH/BTC',12:'LTC/BTC'}
userId_list = [UserName_UserId_dict['maker_lj1'],
                UserName_UserId_dict['maker_lj2'],
                UserName_UserId_dict['maker_lj3']
               ]
userId_test_list = [UserName_UserId_dict['test004'],
                   UserName_UserId_dict['test005'],
                   UserName_UserId_dict['test006']]
rountine_obj = Rountine()
rountine_test_obj = Rountine()
# def index(request):
#     data_list = get_update_data()
#     data = {'data': (data_list)}
#     return render(request, 'index.html', data)

def default_index(request):
    # userId_list = userId_list
    rountine_obj.userId_list = userId_list
    data_list = rountine_obj.get_update_data()
    data = {'data':json.dumps(data_list)}
    return render(request, 'index.html', data)

def testAccount(request):
    rountine_obj.userId_list = userId_test_list
    data_list = rountine_obj.get_update_data()
    data = {'data':json.dumps(data_list)}
    return render(request, 'test_index.html', data)

def order(request):
    minutes_ago = 10
    rountine_obj.userId_list = userId_list
    data = rountine_obj.get_order_relatedData(minutes_ago=minutes_ago)
    return render(request, 'order.html', data)

def testOrder(request):
    minutes_ago = 60
    rountine_obj.userId_list = userId_test_list
    data = rountine_obj.get_order_relatedData(minutes_ago=minutes_ago)
    return render(request, 'order.html', data)

def order_search(request):
    # mongodb_orderTable = rountine_obj.mongodb_orderTable
    start_time_str = request.GET.get('order_startTime')
    start_time = get_timestamp_from_time_str(start_time_str)
    end_time_str = request.GET.get('order_endTime')
    search_list_str = request.GET.get('search')
    search_list = search_list_str.split()
    userId_list = []
    for userName in search_list:
        userId_list.append(UserName_UserId_dict[userName])
    end_time = get_timestamp_from_time_str(end_time_str)
    query = {'timestamp': {'$gt': start_time,'$lt':end_time},'userId':{'$in':userId_list}}

    df = rountine_obj.get_order_df_by_query(query)
    order_detail = rountine_obj.from_df_to_preJson(df)
    orderTime_list = [start_time_str,end_time_str]
    data = {'data':json.dumps(order_detail),'orderTime':json.dumps(orderTime_list),
            'userName_list':json.dumps(search_list)
            }
    return render(request, 'order.html', data)


if __name__ == "__main__":
    order(request=None)
    pass