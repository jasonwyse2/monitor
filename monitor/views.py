from django.shortcuts import render
from monitor.models.bitasset.BitAssetAPI import BitAssetMarketAPI,BitAssetDealsAPI
import json

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
    data = {'data': json.dumps(data_list)}
    return render(request, 'index.html', data)

def default_index(request):

    data_list = get_update_data()
    # print(data_list)
    data = {'data':json.dumps(data_list)}
    return render(request, 'index.html', data)

def get_update_data():

    # mongo_table_balance_list = [cfg.get('mongo_table', 'tradeBalance_ethbtc'),
    #                             cfg.get('mongo_table', 'tradeBalance_bchbtc'),
    #                             cfg.get('mongo_table', 'tradeBalance_ltcbtc')]
    # mongo_table_price = cfg['mongo_table']['realtime_price']
    mongo_table_balance_list = ['tradeBalance_ethbtc','tradeBalance_bchbtc','tradeBalance_ltcbtc']
    mongo_table_price = 'bitasset_RealTrade_price'
    # balance = bitasset.dealApi.accounts_balance()['data']
    # balance1 = bitasset.dealApi1.accounts_balance()['data']
    # balance2 = bitasset.dealApi2.accounts_balance()['data']
    # balance3 = bitasset.dealApi3.accounts_balance()['data']
    # balance_now_list = [balance1, balance2, balance3]
    # print('balance_now_list',balance_now_list)
    tl = time.time()
    now_time = datetime.fromtimestamp(tl).strftime('%Y-%m-%d %H')
    datetime_website = datetime.fromtimestamp(tl).strftime('%Y-%m-%d %H:%M:%S')
    print('datetime_website', datetime_website)
    yes_time = datetime.now() + timedelta(hours=-4)
    yes_time_str = yes_time.strftime('%Y-%m-%d %H')
    balance_yest_list = []
    balance_now_list = []
    for i in range(len(mongo_table_balance_list)):
        doc_yest = mongo_db[mongo_table_balance_list[i]].find_one({'datetime': yes_time_str})['account']
        balance_yest_list.append(doc_yest)
        doc_now = mongo_db[mongo_table_balance_list[i]].find_one({'datetime': now_time})['account']
        balance_now_list.append(doc_now)
    # get exchange rate
    doc = mongo_db[mongo_table_price].find_one({'datetime': now_time})  # {'datetime':now_time}

    price_list = [doc['ethbtc'], doc['bchbtc'], doc['ltcbtc'], doc['btcusdt'], doc['ethusdt'], doc['bchusdt'],
                  doc['ltcusdt']]

    data_list = [balance_now_list, balance_yest_list, price_list, datetime_website]
    return data_list
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
    condiction_list = []
    for contractId in contractId_list:
        condiction_list.append({'contractId':contractId})

    end_time = get_timestamp_from_time_str(end_time_str)
    query = {'timestamp': {'$gt': start_time,'$lt':end_time},'$or':condiction_list}
    cols_dict = {'contractId': 1, 'filledCurrency': 1, 'filledQuantity': 1, 'canceledQuantity': 1,
                 'price': 1, 'quantity': 1, 'side': 1, 'status': 1, 'timestamp': 1,'uuid':1}
    docs = mongo_db[mongo_table].find(query, cols_dict).sort('timestamp', -1)
    df = pd.DataFrame(list(docs))
    df1 = transform_df(df)
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

def get_order_info():
    mongo_table = mongo_table_order
    now_timestamp10 = time.time()
    now_time = int(now_timestamp10 * 1000)

    ndays_ago_timestamp = get_timestamp10_minutes_ago(minutes_ago_num) * 1000

    query = {'timestamp': {'$gt': ndays_ago_timestamp}}
    cols_dict = {'contractId': 1, 'filledCurrency': 1, 'filledQuantity': 1, 'canceledQuantity': 1,
                 'price': 1, 'quantity': 1, 'side': 1, 'status': 1, 'timestamp': 1,'uuid':1}
    docs = mongo_db[mongo_table].find(query, cols_dict).sort('timestamp', -1)
    df = pd.DataFrame(list(docs))
    df1 = transform_df(df)
    data_list_str = df1.to_json(orient="values")
    return data_list_str

def transform_df(df):
    df['timestamp'] = df['timestamp'].apply(from_timestamp13_to_localtime)
    df = df[['timestamp', 'contractId', 'uuid','price', 'filledCurrency', 'filledQuantity', 'canceledQuantity', 'quantity',
             'side', 'status']]
    df.loc[df['side'].values == 1, 'side'] = 'Buy'
    df.loc[df['side'].values == -1, 'side'] = 'Sell'

    df.loc[df['status'].values == 0, 'status'] = 'No'
    df.loc[df['status'].values == 1, 'status'] = 'Part'
    df.loc[df['status'].values == 2, 'status'] = 'Full'
    df.loc[df['status'].values == 3, 'status'] = 'Cancel order'

    for key in contractId_symbolPair_dict:
        df.loc[df['contractId'].values == key, 'contractId'] = contractId_symbolPair_dict[key]
    return df

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