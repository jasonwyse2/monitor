from monitor.models.bitasset.BitAssetAPI import BitAssetMarketAPI,BitAssetDealsAPI
import json
import time
from monitor.models.const import *
from monitor.models.db import *
from pymongo import MongoClient
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
# from apscheduler.schedulers.blocking import BlockingScheduler

class BitAsset:
    marketApi = BitAssetMarketAPI(RESTURL, APIKEY, SECRETKEY)
    dealApi = BitAssetDealsAPI(RESTURL, APIKEY, SECRETKEY)
    dealApi1 = BitAssetDealsAPI(RESTURL_real1, APIKEY_real1, SECRETKEY_real1)
    sql3 = Sqlite3(dataFile='/mnt/data/bitasset/bitasset.sqlite')
    conn = MongoClient("mongodb://localhost:27017/")
    mongo_db = conn.lingjun

    def collect_data_from_sql3_into_mongodb(self, time_interval=60 * 5):
        db = self.mongo_db
        sql3 = self.sql3
        orders = sql3.fetchall()
        df = pd.DataFrame(list(orders))
        orders_list = df.ix[:,0].tolist()
        print(len(orders_list))
        max_msg = orders_list[3]#max(orders_list)
        # content_sql3 = sql3.fetch_after_timestamp(latest_timestamp_mongo)
        while True:
            orders_info_str = self.dealApi.get_orders_info(orders_list[:1])
            orders_info = json.loads(orders_info_str)
            code = orders_info['code']
            if code==0:
                data = orders_info['data']
                # print(data)
                # query = {'uuid':data[]}
                # db['bitasset_order'].update(data)
                # cursor = db.bitasset_order.find()
                # for doc in cursor:
                #     print(doc)
                sql3.insert()
                sql3.delete_orders_before_timestamp(max_msg)
                orders = sql3.fetchall()
                df = pd.DataFrame(list(orders))
                orders_list = df.ix[:, 0].tolist()
                print(len(orders_list))
                break
    def record_balance(self):
        db = self.mongo_db
        tl = time.localtime(time.time())
        format_time = time.strftime("%Y-%m-%d %H", tl)
        print(format_time)
        balance_info = self.dealApi.accounts_balance()
        # values = {'datetime': '2018-08-28 23', 'account': balance_info['data']}
        # query = {'datetime': format_time}
        # db.bitasset_balance.update(query, values, True, False)
        # db.bitasset_balance.insert(values)
        if(balance_info['code']==0):
            values = {'datetime': format_time,'account':balance_info['data']}
            query = {'datetime':format_time}
            db.bitasset_balance.update(query,values,True,False)
        print('record balance')
    def get_history_balance(self,dt=''):
        db = self.mongo_db
        if dt=='':
            tl = time.localtime(time.time())
            time_format = '%Y-%m-%d'
            time_str = time.strftime(time_format, tl)
            curr = datetime.strptime(time_str, time_format)
            deltaTime = -1
            forward = (curr + relativedelta( days=+deltaTime))
            history_time = forward.strftime(time_format)
            # print(history_time)
            query = {'datetime':history_time+' 23'}
        else:
            query = {'datetime': dt + ' 23'}
        res = db.bitasset_balance.find(query)
        for doc in res:
            df = pd.DataFrame(doc['account'])[['currency', 'balance']]
            # print(df)
            break
        return df
    def get_current_balance(self,):
        db = self.mongo_db
        res = db.bitasset_balance.find().sort("datetime", -1).limit(1)
        for doc in res:
            df = pd.DataFrame(doc['account'])[['currency', 'balance']]
            break
        return df

    def get_contractId_by_symbol(self,symbol):
        symbol_dict =self.marketApi.symbols()
        data_list = symbol_dict['data']
        contractId = ''
        for it in data_list:
            if it['name']==symbol:
                contractId = it['id']
                break
        # print(data_list)
        return contractId
def trade_helper(price,quantity):
    side = {'buy': '1', 'sell': '-1'}
    dealApi = bitasset.dealApi1
    result1 = dealApi.trade('10', side['buy'], price, quantity, '1')
    # dict_data = json.loads(result1)
    # print(result1)
    # if dict_data['code'] == 0:
    #     result2 = dealApi.trade('10', side['sell'], price, quantity, '1')
    #     dict_data = json.loads(result2)
    #     if dict_data['code'] != 0:
    #         dealApi.cancel(dict_data['msg'], '10')
    #     else:
    #         print(result2)
    #         pass
if __name__ == "__main__":
    symbol = 'ETH-BTC'
    orderid = '1534139092429211'
    contractId = '10'
    side = {'buy': '1', 'sell': '-1'}
    bitasset = BitAsset()
    print(bitasset.dealApi1.get_all_orders('10'))
    res = bitasset.dealApi1.trade('10', side['buy'], 0.039001, 0.001, '1')
    dict_data = json.loads(res)
    # print(res)
    # time.sleep(1)
    orderid = dict_data['msg']


    ts_now = time.time()
    # local_time = time.strftime('%Y-%m-%d %H:%M:%S.%f', time.localtime(ts_now))
    # local_str_time = datetime.fromtimestamp(ts_now ).strftime('%Y-%m-%d %H:%M:%S.%f')
    #
    # print(local_str_time)
    res = bitasset.dealApi1.cancel(orderid,'10')
    print(res)
    ts_now1 = time.time()
    print((ts_now1-ts_now))
    # local_time = time.strftime('%Y-%m-%d %H:%M:%S.%f', time.localtime(ts_now))
    # local_str_time = datetime.fromtimestamp(ts_now).strftime('%Y-%m-%d %H:%M:%S.%f')
    #
    # print(local_str_time)
    # 定义BlockingScheduler
    # sched = BlockingScheduler()
    # sched.add_job(bitasset.record_balance, 'interval', seconds=30)
    # sched.start()
    # df = bitasset.get_current_balance()
    # print(df)
    # df = bitasset.get_history_balance()
    # print(df)
    # print(df)
    # bitasset.record_balance()
    # bitasset.collect_data_from_sql3_into_mongodb()
    # orders = bitasset.dealApi.get_all_orders(contractId)
    # orders_info = bitasset.dealApi.get_order_info(orderid)
    # print(orders)
    # print(orders_info)
    # print(bitasset.get_contractId_by_symbol(symbol))




