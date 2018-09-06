from django.shortcuts import render
from monitor.models.bitasset.BitAssetAPI import BitAssetMarketAPI,BitAssetDealsAPI
import json
from monitor.models.rountine_for_views import *
from django.http import JsonResponse
from monitor.models.bitasset.BitAssetInterface import *
from monitor.models.bitasset.bitasset_util import BitAsset
from datetime import timedelta
from monitor.models.tool import *
from  django.http import HttpResponse
from configparser import ConfigParser
bitasset = BitAsset()
# Create your views here.
conn = MongoClient("mongodb://localhost:27017/")
mongo_db = conn.lingjun
mongo_table_order = 'bitasset_RealTrade_order'
cfg = ConfigParser()
# test_path = settings.TEST_CONF_DIR
cfg.read('config.ini')
symbolPair_contractId_dict={'ETH/BTC':10,'BCH/BTC':11,'LTC/BTC':12}
contractId_symbolPair_dict={10:'ETH/BTC',11:'BCH/BTC',12:'LTC/BTC'}
minutes_ago_num=60
def index(request):
    data_list = get_update_data()
    data = {'data': (data_list)}
    return render(request, 'index.html', data)

def default_index(request):

    data_list = get_update_data()
    # print(data_list)
    data = {'data':json.dumps(data_list)}
    return render(request, 'index.html', data)


def balance(request):
    data_list = get_update_data()
    data = {'data': json.dumps(data_list), }
    return JsonResponse(data)

def order_search(request):
    mongo_table = mongo_table_order
    start_time_str = request.GET.get('order_startTime')
    # print(start_time_str)
    start_time = get_timestamp_from_time_str(start_time_str)
    end_time_str = request.GET.get('order_endTime')
    symbol_pair_str = request.GET.get('symbol_pair')
    symbol_pair_list = symbol_pair_str.split()
    # print(symbol_pair_list)
    contractId_list=[]
    for symbolPair in symbol_pair_list:
        contractId_list.append(symbolPair_contractId_dict[symbolPair])
    mongo_queryCondiction_list = []
    for contractId in contractId_list:
        mongo_queryCondiction_list.append({'contractId':contractId})

    end_time = get_timestamp_from_time_str(end_time_str)
    query = {'timestamp': {'$gt': start_time,'$lt':end_time},'$or':mongo_queryCondiction_list}
    cols_dict = {'contractId': 1, 'filledCurrency': 1, 'filledQuantity': 1, 'canceledQuantity': 1,
                 'price': 1, 'quantity': 1, 'side': 1, 'status': 1, 'timestamp': 1,'uuid':1}
    docs = mongo_db[mongo_table].find(query, cols_dict).sort('timestamp', -1)
    df = pd.DataFrame(list(docs))
    df1 = adjust_values_in_df(df)
    # print(df1['timestamp'])
    data_list_str = df1.to_json(orient="values")
    orderTime_list = [start_time_str,end_time_str]
    data = {'data':json.dumps(data_list_str),'orderTime':json.dumps(orderTime_list)}
    return render(request, 'order.html', data)
def order(request):
    data_list_str = get_order_info()
    # data = {'data': json.dumps(data_list_str)}
    now_timestamp10 = time.time()
    end_time_str = from_timestamp10_to_localtime(now_timestamp10)
    start_time_timestamp = get_timestamp10_minutes_ago(minutes_ago_num)
    start_time_str = from_timestamp10_to_localtime(start_time_timestamp)
    orderTime_list = [start_time_str, end_time_str]
    data = {'data': json.dumps(data_list_str), 'orderTime': json.dumps(orderTime_list)}
    return render(request, 'order.html', data)

if __name__ == "__main__":
    # timestamp = time.time()
    # local_str_time = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H')
    # print(local_str_time)
    # print(get_price())
    # format_time = time.strftime("%Y-%m-%d %H", time.time())
    # print(format_time)
    # default_index(request=None)
    order(request=None)
    # for i in range(3):
    #     data = balance(request=None)
    #     print(data)
    #     time.sleep(2)