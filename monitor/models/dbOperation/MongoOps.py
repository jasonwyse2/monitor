from monitor.models.bitasset.BitAssetAPI import BitAssetMarketAPI,BitAssetDealsAPI
import json
import time
import hashlib
from monitor.models.dbOperation.Sqlite3 import *
from monitor.models.dbOperation.tool import *
from pymongo import MongoClient
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
# from MarketMakerBasic import WebSocketBasic
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
import gzip
from monitor.models.dbOperation.UserInfo_Conf import UserName_UserId_dict, UserId_UserName_dict, StatusName_StatusCode_dict
import numpy as np
from apscheduler.schedulers.blocking import BlockingScheduler

class Mongo:
    def __init__(self):
        self.conn = MongoClient("mongodb://localhost:27017/")
        # self.sql3 = Sqlite3(dataFile=sql3_datafile)

    def get_mongodb(self,mongodb_name):
        return self.conn[mongodb_name]
    def get_mongodb_table(self,mongodb_name,mongoTable_name):
        return self.conn[mongodb_name][mongoTable_name]

    class User:
        def __init__(self,mongodb_userTable):
            self.mongodb_userTable = mongodb_userTable

        def update(self, userId, APIKEY, SECRETKEY, RESTURL):
            query = {'userId': userId}
            values = {'$set': {'APIKEY': APIKEY, 'SECRETKEY': SECRETKEY, 'RESTURL':RESTURL}}
            self.mongodb_userTable.update(query, values)
            print('update user info (userName:%s) successfully' % (userId))

        def insert(self, userId, userName, APIKEY, APISECRET,RESTURL):
            query = {'userId': userId}
            values = {'userId': userId, 'userName': userName, 'APIKEY': APIKEY, 'SECRETKEY': APISECRET,'RESTURL':RESTURL}
            self.mongodb_userTable.update(query, values, True, False)
            # self.mongo_userTable.update_one(query,values)
            print('add user (userName:%s) successfully into mongodb_user' % (userName))
        def find_one(self, userId):
            query = {'userId': userId}
            userInfo = self.mongodb_userTable.find_one(query)
            return userInfo
        def delete(self, userId):
            query = {'userId': userId}
            self.mongodb_userTable.delete_one(query)

        def get_dealApi(self, userId):
            userInfo_dict = self.find_one(userId)
            dealApi = BitAssetDealsAPI(userInfo_dict['RESTURL'], userInfo_dict['APIKEY'],
                                            userInfo_dict['SECRETKEY'])
            return dealApi

    class Balance:
        def __init__(self,mongodb_balanceTable, dealApi):
            self.mongodb_balanceTable = mongodb_balanceTable
            self.dealApi = dealApi

        def update(self, userId):
            balance_info = self.dealApi.accounts_balance()
            print(balance_info)
            if (balance_info['code'] == 0):
                # print('get balance successfully from remote website server for user:%s'%UserId_UserName_dict[userId])
                format_time = get_local_datetime(format_str="%Y-%m-%d %H:%M:%S")
                format_time_hour = format_time[0:13] #precise to hour
                query = {'userId': userId,'datetime':{'$regex':format_time_hour}}
                values = {'userId': userId, 'datetime': format_time, 'account': balance_info['data']}

                doc_lastRecord = self.find(userId,record_num=1)
                last_account = list(doc_lastRecord)[0]['account']
                df_lastBTCBalance = pd.DataFrame(last_account)
                lastBTCValue = df_lastBTCBalance.loc[df_lastBTCBalance['currency']=='BTC','balance'].values[0]

                new_account = balance_info['data']
                df_newBTCBalance = pd.DataFrame(new_account)
                newBTCValue = df_newBTCBalance.loc[df_newBTCBalance['currency']=='BTC','balance'].values[0]

                if(lastBTCValue!=newBTCValue):
                    values = {'userId':userId,'datetime': format_time, 'account': balance_info['data'],'change':1}
                # doc = self.mongodb_balanceTable.find_one(query)
                self.mongodb_balanceTable.update(query, values, True, False)
                print('insert balance successfully into mongodb for user:%s ' % UserId_UserName_dict[userId])
            else:
                print('get balance from remote server go wrong:',balance_info)

        def find(self,userId,record_num):
            query = {'userId': userId}  # db.foo.find().sort({_id:1}).limit(50);
            docs = self.mongodb_balanceTable.find(query).sort('_id', -1).limit(record_num)
            # print(list(docs))
            return docs
        def find_by_datetime(self,userId,datetime):
            query  = {'userId': userId,'datetime':{'$lt':datetime}}
            docs = self.mongodb_balanceTable.find(query).sort('datetime',-1).limit(1)
            return docs
        def delete(self, userId):
            pass

    class Order:
        def __init__(self,mongodb_orderTable, dealApi):
            self.mongodb_orderTable = mongodb_orderTable
            self.dealApi = dealApi
        def insert(self, orderId_list):
            if(len(orderId_list))==0:
                return
            else:
                while True:
                    orders_info_str = self.dealApi.get_orders_info(orderId_list)
                    orders_info = json.loads(orders_info_str)
                    code = orders_info['code']
                    if code == 0:
                        data = orders_info['data']
                        orderInfo_df = pd.DataFrame(data)
                        # select the done order out, 2:full ,3:cancel
                        full_code = StatusName_StatusCode_dict['full']
                        cancel_code = StatusName_StatusCode_dict['cancel']
                        order_full_df = orderInfo_df[orderInfo_df['status'] == full_code]

                        order_cancel_df =  orderInfo_df[(orderInfo_df['status'] == cancel_code)]
                        order_partCancel_df = order_cancel_df.loc[(orderInfo_df['filledQuantity'].values>0) & (orderInfo_df['canceledQuantity'].values>0)]
                        order_partCancel_df['status'] = StatusName_StatusCode_dict['part-cancel']


                        order_cancel_df = order_cancel_df.copy()
                        order_cancel_df.loc[(orderInfo_df['filledQuantity'] > 0) & (orderInfo_df['canceledQuantity'] > 0),'status']\
                            =StatusName_StatusCode_dict['part-cancel']


                        order_done_df = pd.concat([order_full_df,order_cancel_df])
                        order_done_df.reset_index(inplace=True)
                        done_order_list = order_done_df.to_dict(orient='records')

                        if len(done_order_list) > 0:
                            self.mongodb_orderTable.insert(done_order_list)
                        break

            insert_orderId_list = order_done_df['uuid'].values.tolist()
            return insert_orderId_list

        def saveOrder(self,mongo_obj,sql3_obj,userId_list):

            mongodb_userTable = mongo_obj.get_mongodb_table(mongodb_name='bitasset', mongoTable_name='user')
            mongodb_orderTable = mongo_obj.get_mongodb_table(mongodb_name='bitasset', mongoTable_name='order')
            num_read_from_sql3 = 300
            for i in range(len(userId_list)):
                userId = userId_list[i]
                orderId_list0 = sql3_obj.fetch_specific_num(userId, num=num_read_from_sql3)
                if orderId_list0:
                    orderId_list = pd.DataFrame(orderId_list0).iloc[:, 0].values.tolist()
                    user_obj = Mongo.User(mongodb_userTable)
                    dealApi = user_obj.get_dealApi(userId)
                    order_obj = Mongo.Order(mongodb_orderTable, dealApi)
                    insert_orderId_list = order_obj.insert(orderId_list)
                    print('insert into mongodb items', len(insert_orderId_list))
                    sql3_obj.delete_by_userId_orderIdlist(userId, insert_orderId_list)
            print('------------- save order is over. --------------')

        def find(self,num):
            pass
    class Exchange():
        def __init__(self,exchangeName,mongodb_exchangeTable):
            self.mongodb_exchangeTable = mongodb_exchangeTable
            self.exchangeName = exchangeName
        def update(self, price_dict):
            print('going to update "price_dict" in mongodb:',price_dict)
            format_time = get_local_datetime(format_str="%Y-%m-%d %H:%M:%S")
            format_time_hour = format_time[0:13]  # precise to hour
            query = {'datetime': {'$regex':format_time_hour}}
            values = {'datetime': format_time,'exchangeName':self.exchangeName}
            exchangeRate_dict = {'exchangePrice':price_dict}
            values.update(exchangeRate_dict)
            print(' "price_dict" going to write in mongodb:',values)
            self.mongodb_exchangeTable.insert(query, values, True, False)
        def find(self,record_num,exchangeName='huobi'):
            query = {'exchangeName':exchangeName}
            # self.mongodb_exchangeTable.update(query, values, True, False)
            docs = self.mongodb_exchangeTable.find(query).sort('_id', -1).limit(record_num)
            # for doc in docs:
            #     print(doc)
            return docs


if __name__ == "__main__":

    mongodb_name = 'bitasset'
    mongodb_orderTable_name = 'order'
    mongodb_balanceTable_name = 'balance'
    mongodb_userTable_name = 'user'
    mongodb_exchangeTable_name = 'exchange'
    sql3_datafile= '/mnt/data/bitasset/bitasset0906.sqlite'
    dbOps_obj = Mongo()

    # ----  store data in mongo

    mongodb_exchangeTable = dbOps_obj.get_mongodb_table(mongodb_name, mongodb_exchangeTable_name)
    mongodb_balanceTable = dbOps_obj.get_mongodb_table(mongodb_name, mongodb_balanceTable_name)






