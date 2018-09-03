import sqlite3
class Sqlite3:
    tableName = 'bitasset_orderId'
    def __init__(self, dataFile=None):
        if dataFile is None:
            self.conn = sqlite3.connect(":memory:")
        else:
            try:
                self.conn = sqlite3.connect(dataFile)
            except sqlite3.Error as e:
                print("连接sqlite数据库失败:", e.args[0])
        self.create_table()

    def getcursor(self):
        return self.conn.cursor()

    def drop(self, table):
        '''
        if the table exist,please be carefull
        '''
        if table is not None and table != '':
            cu = self.getcursor()
            sql = 'DROP TABLE IF EXISTS ' + table
            try:
                cu.execute(sql)
            except sqlite3.Error as why:
                print("delete table failed:", why.args[0])
                return
            self.conn.commit()
            print("delete table successful!")
            cu.close()
        else:
            print("table does not exist！")

    def create_table(self,):
        '''
        create database table
        :param sql:
        :return:
        '''
        tableName = self.tableName
        sql = 'create table if not exists '+tableName+' (' \
                                 'orderid CHAR(100))'
        if sql is not None and sql != '':
            cu = self.getcursor()
            try:
                cu.execute(sql)
            except sqlite3.Error as why:
                print("create table failed:", why.args[0])
                return
            self.conn.commit()
            print("create table successful!")
            cu.close()
        else:
            print("sql is empty or None")

    def insert(self, data):
        '''
        insert data to the table
        :param sql:
        :param data:
        :return:
        '''
        sql = 'INSERT INTO ' + self.tableName + '(orderid) values (?)'
        if sql is not None and sql != '':
            if data is not None:
                cu = self.getcursor()
                try:
                    for d in data:
                        cu.execute(sql, [d])
                        self.conn.commit()
                except sqlite3.Error as why:
                    print("insert data failed:", why.args[0])
                cu.close()
        else:
            print("sql is empty or None")

    def fetch_specific_num(self,num,sql=''):
        '''
                query all data
                :param sql:
                :return:
                '''
        if sql == '':
            sql = 'SELECT * FROM ' + self.tableName +' limit ?'
        if sql is not None and sql != '':
            cu = self.getcursor()
            content = None
            try:
                cu.execute(sql,[num,])
                content = cu.fetchall()
            except sqlite3.Error as why:
                print("fetchall data failed:", why.args[0])
            cu.close()
            return content
        else:
            print("sql is empty or None")
    def fetchall(self, sql=''):
        '''
        query all data
        :param sql:
        :return:
        '''
        if sql=='':
            sql = 'SELECT * FROM ' + self.tableName
        if sql is not None and sql != '':
            cu = self.getcursor()
            content = None
            try:
                cu.execute(sql)
                content = cu.fetchall()

            except sqlite3.Error as why:
                print("fetchall data failed:", why.args[0])
            cu.close()
            return content
        else:
            print("sql is empty or None")

    def fetchone(self, sql, data):
        '''
        query one data
        :param sql:
        :param data:
        :return:
        '''
        if sql is not None and sql != '':
            if data is not None:
                cu = self.getcursor()
                try:
                    d = (data,)
                    cu.execute(sql, d)
                    content = cu.fetchall()

                except sqlite3.Error as why:
                    print("fetch the data failed:", why.args[0])
                    return
                cu.close()
        else:
            print("sql is empty or None")

    def update(self, sql, data):
        '''
        update the data
        :param sql:
        :param data:
        :return:
        '''
        if sql is not None and sql != '':
            if data is not None:
                cu = self.getcursor()
                try:
                    for d in data:
                        cu.execute(sql, d)
                        self.conn.commit()
                except sqlite3.Error as why:
                    print("update data failed:", why.args[0])
                cu.close()
        else:
            print ("sql is empty or None")

    def delete(self, sql, data=None):
        '''
        delete the data
        :param sql:
        :param data:
        :return:
        '''
        if sql is not None and sql != '':
            cu = self.getcursor()
            if data is not None:
                try:
                    for d in data:
                        cu.execute(sql, d)
                        self.conn.commit()
                except sqlite3.Error as why:
                    print("delete data failed:", why.args[0])
            else:
                try:
                    cu.execute(sql)
                    self.conn.commit()
                except sqlite3.Error as why:
                    print ("delete data failed:", why.args[0])
            cu.close()
        else:
            print ("sql is empty or None")
    def delete_orders_before_timestamp(self, timestamp):
        sql = 'delete from '+self.tableName+' where orderid<= ?'
        cu = self.getcursor()
        try:
            cu.execute(sql,[timestamp,])
            self.conn.commit()
        except sqlite3.Error as why:
            print("delete data failed:", why.args[0])
    def delete_all(self,):
        sql = 'delete from '+self.tableName
        cu = self.getcursor()
        cu.execute(sql)
        self.conn.commit()
        cu.close()
    def __del__(self):
        self.conn.close()

if __name__ == "__main__":
    # sql3 = Sqlite3(dataFile='/mnt/data/bitasset/bitasset.sqlite')
    sql3 = Sqlite3(dataFile='/mnt/data/bitasset/bitasset.sqlite')
    # sql3.insert(data)
    res = sql3.fetchall()
    print(res)

