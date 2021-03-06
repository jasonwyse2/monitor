from datetime import datetime,timedelta
import time
def from_timestamp13_to_localtime(timestamp):
    local_str_time = datetime.fromtimestamp(timestamp / 1000.0).strftime('%Y-%m-%d %H:%M:%S.%f')
    return str(local_str_time)[:-7]
def from_timestamp10_to_localtime(timestamp,format_str ='%Y-%m-%d %H:%M:%S' ):
    local_str_time = datetime.fromtimestamp(timestamp).strftime(format_str)
    return str(local_str_time)
def get_timestamp10_minutes_ago(num):
    days_ago = (datetime.now() - timedelta(minutes=num))
    timeStamp = int(time.mktime(days_ago.timetuple()))
    return timeStamp
def get_timestamp_from_time_str(time_str):
    st = time.strptime(time_str, '%Y-%m-%d %H:%M:%S')

    timestamp = int(time.mktime(st))*1000
    return timestamp
def get_local_datetime(format_str='%Y-%m-%d %H:%M:%S'):
    timestamp10 = time.time()
    tl = time.localtime(timestamp10)
    format_time = time.strftime(format_str, tl)
    return format_time
if __name__ == "__main__":
    ts = 1536731100791
    time_str = '2018-09-01 23:11:01'
    print(from_timestamp13_to_localtime(ts))
    print(get_timestamp_from_time_str(time_str))