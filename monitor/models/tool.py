from datetime import datetime,timedelta
import time
def from_timestamp13_to_localtime(timestamp):
    local_str_time = datetime.fromtimestamp(timestamp / 1000.0).strftime('%Y-%m-%d %H:%M:%S.%f')
    return str(local_str_time)[:-3]
def from_timestamp10_to_localtime(timestamp):
    local_str_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    return str(local_str_time)
def get_timestamp10_minutes_ago(num):
    days_ago = (datetime.now() - timedelta(minutes=num))
    timeStamp = int(time.mktime(days_ago.timetuple()))
    return timeStamp
def get_timestamp_from_time_str(time_str):
    st = time.strptime(time_str, '%Y-%m-%d %H:%M:%S')

    timestamp = int(time.mktime(st))*1000
    return timestamp
if __name__ == "__main__":
    time_str = '2018-09-01 23:11:01'
    print(get_timestamp_from_time_str(time_str))