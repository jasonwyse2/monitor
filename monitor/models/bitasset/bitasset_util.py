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
    dealApi2 = BitAssetDealsAPI(RESTURL_real2, APIKEY_real2, SECRETKEY_real2)
    dealApi3 = BitAssetDealsAPI(RESTURL_real3, APIKEY_real3, SECRETKEY_real3)
    dataFile = ''
    sql3 = Sqlite3(dataFile='/mnt/data/bitasset/bitasset.sqlite')
    conn = MongoClient("mongodb://localhost:27017/")
    mongo_db = conn.lingjun

    def collect_data_from_sql3_into_mongodb(self, time_interval=60 * 5):
        db = self.mongo_db
        sql3 = self.sql3
        # orders = sql3.fetchall()
        orders = sql3.fetch_specific_num(num=10)
        df = pd.DataFrame(list(orders))
        orders_list = df.ix[:,0].tolist()
        print(len(orders_list))
        max_msg = max(orders_list)#orders_list[3]#max(orders_list)
        # content_sql3 = sql3.fetch_after_timestamp(latest_timestamp_mongo)
        while True:
            orders_info_str = self.dealApi.get_orders_info(orders_list)
            orders_info = json.loads(orders_info_str)
            code = orders_info['code']
            if code==0:
                data = orders_info['data']
                # print(data)
                # db['bitasset_order'].insert(data)
                # cursor = db.bitasset_order.find()
                # for doc in cursor:
                #     print(doc)
                sql3.delete_orders_before_timestamp(max_msg)
                # orders = sql3.fetchall()
                # df = pd.DataFrame(list(orders))
                # orders_list = df.ix[:, 0].tolist()
                # print(len(orders_list))
                break
    def record_balance(self):
        db = self.mongo_db
        tl = time.localtime(time.time())
        format_time = time.strftime("%Y-%m-%d %H", tl)
        print(format_time)
        balance_info = self.dealApi.accounts_balance()
        # print(balance_info)
        # values = {'datetime': '2018-08-28 23', 'account': balance_info['data']}
        # query = {'datetime': format_time}
        # db.bitasset_balance.update(query, values, True, False)
        # db.bitasset_balance.insert(values)
        if(balance_info['code']==0):
            values = {'datetime': format_time,'account':balance_info['data']}
            query = {'datetime':format_time}
            db.bitasset_balance.update(query,values,True,False)
        print('record balance successfully')
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

if __name__ == "__main__":
    symbol = 'ETH-BTC'
    orderid_list = ['1535548063787068','1535548063787069'] #'1535548063786492'
    orderid2 = '1535548063787068'
    orderid3 = '1535548063787069'
    contractId = '10'

    bitasset = BitAsset()
    # 定义BlockingScheduler
    # sched = BlockingScheduler()
    # sched.add_job(bitasset.record_balance, 'interval', seconds=30)
    # sched.start()
    # 定义BlockingScheduler
    # sched = BlockingScheduler()
    # sched.add_job(bitasset.record_balance, 'interval', seconds=30)
    # sched.start()
    # df = bitasset.get_current_balance()
    # print(df)
    # df = bitasset.get_history_balance()
    # print(df)
    # print(df)
    # ts_now = 1535606754502
    # local_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts_now/1000))
    # print(local_time)
    # bitasset.record_balance()
    bitasset.collect_data_from_sql3_into_mongodb()
    # orders = bitasset.dealApi.get_all_orders(contractId)
    # for orderid in orderid_list:
    #     orders_info = bitasset.dealApi.get_order_info(orderid)
    #     data = orders_info['data']
    #     ts = data['timestamp']
    #     local_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts / 1000))
    #     print(local_time)
    #     print(data)
        # local_dt_time = datetime.fromtimestamp(data['timestamp'])
    #     # print(local_dt_time)
    #     print(data['timestamp'])
    # print(orders_info)
    # print(orders)
    # print(orders_info)
    # print(bitasset.get_contractId_by_symbol(symbol))




