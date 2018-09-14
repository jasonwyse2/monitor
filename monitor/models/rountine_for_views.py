from django.shortcuts import render
from monitor.models.bitasset.BitAssetAPI import BitAssetMarketAPI,BitAssetDealsAPI
import json
from django.http import JsonResponse
from pymongo import MongoClient
from monitor.models.bitasset.BitAssetInterface import *
from monitor.models.bitasset.bitasset_util import BitAsset
from datetime import timedelta
from monitor.models.dbOperation.tool import *
from  django.http import HttpResponse
from configparser import ConfigParser
from monitor.models.dbOperation.MongoOps import Mongo
from monitor.models.dbOperation.UserInfo_Conf import UserId_UserName_dict,\
    UserName_UserId_dict,ContractId_SymbolPair_dict,StatusCode_StatusName_dict

class Rountine:
    listen_exchangeName = 'huobi'
    mongodb_name = 'bitasset'
    mongodb_orderTable_name = 'order'
    mongodb_balanceTable_name = 'balance'
    mongodb_userTable_name = 'user'
    mongodb_exchangeTable_name = 'exchange'
    sql3_datafile= '/mnt/data/bitasset/bitasset0906.sqlite'
    dbOps_obj = Mongo()

    mongodb_exchangeTable = dbOps_obj.get_mongodb_table(mongodb_name, mongodb_exchangeTable_name)
    mongodb_userTable = dbOps_obj.get_mongodb_table(mongodb_name, mongodb_userTable_name)
    mongodb_balanceTable = dbOps_obj.get_mongodb_table(mongodb_name, mongodb_balanceTable_name)
    mongodb_orderTable = dbOps_obj.get_mongodb_table(mongodb_name, mongodb_orderTable_name)
    exchange_obj = Mongo.Exchange(listen_exchangeName, mongodb_exchangeTable)
    user_obj = Mongo.User(mongodb_userTable)

    userId_list = [123,124,125]
    minutes_ago = 60*24*2
    def __init__(self):
        # self.userId_list = userId_list
        pass

    def get_update_data(self):
        docs = self.exchange_obj.find(record_num=1, exchangeName=self.listen_exchangeName)
        price_dict={}
        exchangePrice_datetime = 'go wrong with time'
        for doc in docs:
            price_dict = doc['exchangePrice']
            exchangePrice_datetime = doc['datetime']
        # price_dict = list(docs)[0]['exchangePrice']
        print('price_dict:',price_dict)
        df_price = pd.DataFrame([price_dict])
        # exchangePrice_datetime = price_dict['datetime']
        df_price_dict = json.loads(df_price.to_json(orient='split'))

        account_datetime_list = []
        balanceTable_dict = {}

        def transfor_currency_into_BTC(x):
            currency_in_BTC = 0.0
            currency, balance = x[0], x[1]
            if currency.upper() in ['BCH','ETH','LTC']:
                price_key = currency.lower() + 'btc'
                exchange_rate = price_dict[price_key]
                if exchange_rate != None:
                    currency_in_BTC = exchange_rate * float(balance)
            elif currency.upper()== 'BTC':
                currency_in_BTC = float(balance)
            elif currency.upper()== 'USDT':
                price_key = 'btcusdt'
                exchange_rate = 1/price_dict[price_key]
                currency_in_BTC = exchange_rate * float(balance)
            else:
                currency_in_BTC = float(balance)
            return currency_in_BTC

        for userId in self.userId_list:
            dealApi = self.user_obj.get_dealApi(userId)
            balance_obj = Mongo.Balance(self.mongodb_balanceTable,dealApi)
            docs = balance_obj.find(userId,record_num=1)
            for item in docs:
                # print(item)
                data_dict = item
                break
            # data_dict = list(docs)[0]
            print('docs:',data_dict)
            balancdInfo_new_dict = data_dict
            account_datetime = balancdInfo_new_dict['datetime']
            account_datetime_list.append(account_datetime)
            account_new = balancdInfo_new_dict['account']
            df_account_new = pd.DataFrame(account_new)
            timestamp_old = get_timestamp10_minutes_ago(num=self.minutes_ago)
            local_date_str = from_timestamp10_to_localtime(timestamp_old, format_str='%Y-%m-%d')
            # local_date_str = get_local_datetime(format_str='%Y-%m-%d')

            lastDay_datetime = local_date_str + ' 00:00:00'
            docs = balance_obj.find_by_datetime(userId,lastDay_datetime)
            for doc in docs:
                balancdInfo_old_dict = doc
                break
            # balancdInfo_old_dict = list(docs)[0]
            account_old = balancdInfo_old_dict['account']
            df_account_old = pd.DataFrame(account_old)

            df_account_old.rename(columns={'available': 'available_old', 'balance': 'balance_old', 'frozen': 'frozen_old'},
                          inplace=True)

            df_account_now_old = pd.merge(df_account_new, df_account_old, on='currency', how='left')
            df_account_now_old = df_account_now_old.loc[(df_account_now_old['currency']=='BTC')|
                                                        (df_account_now_old['currency']=='BCH')|
                                                        (df_account_now_old['currency']=='ETH')|
                                                        (df_account_now_old['currency']=='LTC')|
                                                        (df_account_now_old['currency'] == 'USDT')
                                                        # (df_account_now_old['currency'] == 'CNYT')

            ]
            df_account_now_old['newBalance_in_BTC'] = df_account_now_old[['currency', 'balance']].apply(transfor_currency_into_BTC, axis=1)
            df_account_now_old['oldBalance_in_BTC'] = df_account_now_old[['currency', 'balance_old']].apply(transfor_currency_into_BTC, axis=1)

            df_account_now_old['PNL'] = (df_account_now_old['newBalance_in_BTC'].values) - df_account_now_old['oldBalance_in_BTC'].values

            df_return = df_account_now_old[['currency', 'frozen', 'available', 'balance', 'newBalance_in_BTC', 'PNL']]

            df = df_return.rename(
                columns={'currency': 'Currency', 'frozen': 'Frozen', 'available': 'Available', 'balance': 'Balance',
                         'newBalance_in_BTC': 'BTC Value'})

            balanceTable_dict[UserId_UserName_dict[userId]] = json.loads(df.to_json(orient='split'))
            data_list = [df_price_dict, exchangePrice_datetime, balanceTable_dict, account_datetime_list]

        return data_list

    def get_order_df_by_query(self,query):
        cols_dict = {'timestamp': 1, 'userId': 1, 'contractId': 1, 'uuid': 1, 'side': 1, 'quantity': 1,
                     'filledQuantity': 1, 'price': 1, 'filledCurrency': 1, 'status': 1,
                     # 'orderType': 1
                     }
        docs = self.mongodb_orderTable.find(query, cols_dict).sort('timestamp', -1)
        df = pd.DataFrame(list(docs))
        return df
    def from_df_to_preJson(self,df):
        if df.shape[0]>0:
            df = self.adjust_values_in_df(df)
            order_detail = json.loads(df.to_json(orient="split"))
        else:
            order_detail={}
        return order_detail
    def get_order_detail(self, minutes_ago=5):
        # mongo_table = self.mongodb_orderTable
        ndays_ago_timestamp = get_timestamp10_minutes_ago(minutes_ago) * 1000

        query = {'timestamp': {'$gt': ndays_ago_timestamp},'userId':{'$in':self.userId_list}}
        # cols_dict = {'contractId': 1, 'filledCurrency': 1, 'filledQuantity': 1, 'orderType': 1,
        #              'price': 1, 'quantity': 1, 'side': 1, 'status': 1, 'timestamp': 1,'uuid':1,'userId':1}
        # cols_dict = {'timestamp': 1,'userId': 1,'contractId': 1, 'uuid': 1,'side': 1, 'quantity': 1,
        #               'filledQuantity': 1, 'price': 1,'filledCurrency': 1,'status': 1,
        #                  # 'orderType': 1
        #              }
        # docs = mongo_table.find(query, cols_dict).sort('timestamp', -1)
        # df = pd.DataFrame(list(docs))
        df = self.get_order_df_by_query(query)
        order_detail = self.from_df_to_preJson(df)
        return order_detail

    def get_order_relatedData(self,minutes_ago):
        order_detail = self.get_order_detail(minutes_ago)
        now_timestamp10 = time.time()
        end_time_str = from_timestamp10_to_localtime(now_timestamp10)
        start_time_timestamp = get_timestamp10_minutes_ago(minutes_ago)
        start_time_str = from_timestamp10_to_localtime(start_time_timestamp)
        orderTime_list = [start_time_str, end_time_str]
        userName_list = []
        for userId in self.userId_list:
            userName_list.append(UserId_UserName_dict[userId])
        data = {'data': json.dumps(order_detail), 'orderTime': json.dumps(orderTime_list),
                'userName_list':json.dumps(userName_list)}
        return data

    def adjust_values_in_df(self,df):
        df['timestamp'] = df['timestamp'].apply(from_timestamp13_to_localtime)
        df = df[['timestamp', 'userId','contractId','uuid','side','quantity',
                 'filledQuantity','price','filledCurrency', 'status']]

        df.loc[df['side'].values == 1, 'side'] = 'Buy'
        df.loc[df['side'].values == -1, 'side'] = 'Sell'
        for key in UserId_UserName_dict:
            df.loc[df['userId'].values == key, 'userId'] = UserId_UserName_dict[key]

        for key in StatusCode_StatusName_dict:
            df.loc[df['status'].values == key, 'status'] = StatusCode_StatusName_dict[key]

        # df.loc[df['status'].values == 0, 'status'] = 'No'
        # df.loc[df['status'].values == 1, 'status'] = 'Part'
        # df.loc[df['status'].values == 2, 'status'] = 'Full'
        # df.loc[df['status'].values == 3, 'status'] = 'Cancel'
        # df.loc[df['status'].values == 4, 'status'] = 'Part-Canceled'

        for key in ContractId_SymbolPair_dict:
            df.loc[df['contractId'].values == key, 'contractId'] = ContractId_SymbolPair_dict[key]

        df = df.rename(
            columns={'userId': 'userName', 'contractId': 'pair', 'uuid': 'orderId'})
        return df

if __name__ == "__main__":
    rountine = Rountine()
    rountine.userId_list = [UserName_UserId_dict['test005']]
    data_list = rountine.get_order_detail(minutes_ago=10)
    print(data_list)
