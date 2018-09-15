#!/usr/bin/python
# encoding: utf-8

import argparse
import time
import socket
import struct
import logging
import logging.handlers
import signal
from datetime import datetime

__VERSION__ = '0.2.0'


def current_time():
    t = datetime.fromtimestamp(time.time())
    return t.strftime('%Y%m%d-%H:%M:%S')


def conn_tcp(dst_host, dst_port, timeout, src_host=None, src_port=None, rst=False):
    """
    open a tcp connection to host:port
    return conn time,close time and error(if exist)
    :param dst_host: remote host
    :param dst_port: remote port
    :param src_host: local host
    :param src_port: local port
    :param rst: if set,use RESET to close connection
    :param timeout: wait TIMEOUT second in connection period
    :return: (conn_time, close_time, err),connection time,close time and error message
    """

    (t1, t2, t3, te, conn_time, close_time, err, local_addr) = (-1, -1, -1, -1, -1, -1, '', None)
    # 若指定了RST参数，那么开始设定相关参数
    if rst:
        l_onoff = 1
        l_linger = 0
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 开始设定发送RST需要的参数
        if rst:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                         struct.pack('ii', l_onoff, l_linger))
        if src_host and src_port and src_port < 65536:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            socket.socket.bind(s, (src_host, int(src_port)))
        t1 = time.time()
        s.settimeout(timeout)
        s.connect((dst_host, int(dst_port)))
        local_addr = s.getsockname()
        t2 = time.time()
        s.close()
        t3 = time.time()
    except Exception, e:
        local_addr = s.getsockname()
        err = e
        te = time.time()
    finally:
        try:
            s.close()
        except Exception, e2:
            print e2

    if t2 >= 0:
        conn_time = t2 - t1
    if t3 >= 0:
        close_time = t3 - t2
    if te >= 0:
        if t2 >= 0:
            conn_time = t2 - t1
            close_time = t3 - t2
        else:
            conn_time = te - t1
    return (conn_time, close_time, err, local_addr)


def judge_count(count):
    if count is not None:
        return count > 0
    else:
        return True


def judge_args(argument):
    # 检查本机地址和本地端口是否按规则给出
    if bool(argument.src_host) ^ (bool(argument.src_port) or bool(argument.src_rotate_port)):
        tip = 'src_host and src_port(src_rotate_port) must be given at the same time'
        print tip
        mylogger.error(tip)
        return False
    else:
        return True


def go(dst_host, dst_port, timeout, interval, src_host=None, src_port=None, count=None, src_rotate_port=None, rst=False,log_to_file=False
       ):
    error_flag = False
    if src_rotate_port:
        src_port = src_rotate_port

    while judge_count(count):
        (conn_time, close_time, err, local_addr) = conn_tcp(dst_host, dst_port, timeout=timeout, src_host=src_host,
                                                            src_port=src_port, rst=rst)
        result.put(conn_time, True if len(str(err)) == 0 else False)
        # 初始化存放输出信息的列表
        output = list()
        if local_addr:
            output.append(local_addr[0] + ':' + str(local_addr[1]))
        output.append(dst_host + ':' + str(dst_port))
        if conn_time >= 0:
            output.append('conn_time: ' + str('%.6f' % conn_time))
        if close_time >= 0:
            pass
            # output.append('close_time: ' + str('%.6f' % close_time))
        if len(str(err)) > 0:
            error_flag = True
            output.append('ERROR: ' + str(err))

        final_output = ', '.join(output)
        # print final_output
        if error_flag:
            mylogger.error(final_output)
        else:
            mylogger.info(final_output)

        # 清除错误标志，执行本次循环的收尾工作
        err = ''
        error_flag = False
        del output

        # 检查是否需要源端口自增
        if src_rotate_port:
            src_port += 1
        if src_port >= 65536:
            tip_reach_65535 = 'Local port reach 65535,reset src port to 1024.'
            print tip_reach_65535
            mylogger.warning(tip_reach_65535)
            src_port = 1024

        # 若有 count，自减1
        if count is not None:
            count -= 1

        # 连接间隔
        time.sleep(interval)


def initial(arguments):
    signal.signal(signal.SIGINT, my_exit)
    signal.signal(signal.SIGTERM, my_exit)

    # 开启log记录
    # logging.basicConfig(level=logging.DEBUG,
    #                     format='%(levelname)s: %(asctime)s - %(filename)s[line:%(lineno)d] -  %(message)s',
    #                     filename='tcpping2_' + arguments.dst_host[0] + '_' + str(arguments.dst_port[0]) + '.log',
    #                     filemode='w')


def get_version():
    return __VERSION__


def getargs():
    tail_str = """examples:
    tcpping2.py 192.168.1.25 80"""
    parser = argparse.ArgumentParser(
        prog='tcpping2',
        description='A tiny tool to connect target using TCP Connection. Version:' + __VERSION__,
        epilog=tail_str)

    # 本地IP地址
    parser.add_argument('-H', '--src-host', dest='src_host', help='Set local IP', type=str)
    # 本地源端口
    parser.add_argument('-P', '--src-port', dest='src_port', help="Set local port", type=int)
    # 本地源端口，自增的进行连接，一般用来地毯式的查找本地有问题的源端口
    parser.add_argument('-L', '--src-rotate-port', dest='src_rotate_port', help="Set local port(rotate)", type=int)
    # 连接间隔
    parser.add_argument('-i', '--interval', dest='interval', help="Set connection interval(second),default==2", type=float)
    # 连接超时时间
    parser.add_argument('-t', '--timeout', dest='timeout', help="Set timeout(second),default==5", type=float)
    # 总的连接次数
    parser.add_argument('-c', '--count', dest='count', help="Stop after sending count packets", type=int)
    # 是否以RESET断开连接，可以加快两端的系统回收连接
    parser.add_argument('-R', '--rst', dest='rst', action='store_true',
                        help="Sending reset to close connection instead of FIN")
    # 是否需要输出log日志
    parser.add_argument('-l', '--log', dest='log', action='store_true',
                        help="Set to write log file to disk")
    # 连接的目标主机
    parser.add_argument('dst_host', nargs=1, action='store',help='Target host or IP')
    # 连接的目标端口
    parser.add_argument('dst_port', nargs=1, action="store", type=int,help='Target port')

    return parser.parse_args()


def my_exit(signum, frame):
    result_string = result.get_statistics()
    mylogger.info(result_string)
    exit()


class ResultBucket:
    is_initialled = False
    ok_count = 0
    error_count = 0
    min_time = 0.0
    max_time = 0.0
    avg_time = 0.0

    def __init__(self, dst_host, dst_port):
        self.dst_host = dst_host
        self.dst_port = dst_port
        pass

    def put(self, conn_time, status):
        if status == False:
            self.error_count += 1
        else:
            if self.is_initialled == False:
                self.min_time = self.max_time = self.avg_time = conn_time
                self.is_initialled = True
            else:
                if conn_time < self.min_time:
                    self.min_time = conn_time
                if conn_time > self.max_time:
                    self.max_time = conn_time
                self.avg_time = (self.avg_time * self.ok_count + conn_time) / (self.ok_count + 1)

            self.ok_count += 1

    def get_statistics(self):
        format_string = """--- {dst_host}:{dst_port} tcpping statistics ---
{total_count} packets transmitted, {ok_count} connected, {error_rate}% connection failed
min/avg/max = {min_time}/{avg_time}/{max_time} ms"""

        format_dict = dict()
        format_dict['dst_host'] = self.dst_host
        format_dict['dst_port'] = self.dst_port
        format_dict['total_count'] = self.ok_count + self.error_count
        format_dict['ok_count'] = self.ok_count
        format_dict['error_rate'] = self.error_count / (self.ok_count + self.error_count) * 100
        format_dict['min_time'] = str('%.6f' % self.min_time)
        format_dict['avg_time'] = str('%.6f' % self.avg_time)
        format_dict['max_time'] = str('%.6f' % self.max_time)
        return format_string.format(**format_dict)


if __name__ == '__main__':
    args = getargs()
    result = ResultBucket(args.dst_host[0], args.dst_port[0])

    # 设置输出的日志格式
    console_formatter = logging.Formatter('[%(asctime)s] %(message)s')
    file_formatter = logging.Formatter('%(levelname)s: %(asctime)s - %(filename)s[line:%(lineno)d] -  %(message)s')

    # 设置输出到屏幕的handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)

    # 创建logging
    mylogger = logging.getLogger('tcpping2')
    mylogger.setLevel(logging.INFO)

    # 加入handler
    mylogger.addHandler(console_handler)

    # 判断一下是否需要打log文件
    if args.log:
        # 设置输出到文件的handler
        file_handler = logging.handlers.RotatingFileHandler(
            'tcpping2_' + args.dst_host[0] + '_' + str(args.dst_port[0]) + '.log', mode='w',
            maxBytes=10*1024*1024, backupCount=5)
        file_handler.setFormatter(file_formatter)
        mylogger.addHandler(file_handler)




    initial(args)
    if judge_args(args):
        go(args.dst_host[0], args.dst_port[0], timeout=args.timeout if args.timeout else 5,
           interval=args.interval if args.interval else 2,
           src_host=args.src_host if args.src_host else None, src_port=args.src_port if args.src_port else 0,
           src_rotate_port=args.src_rotate_port if args.src_rotate_port else None, rst=args.rst if args.rst else None,
           count=args.count if args.count else None)
        print result.get_statistics()
    else:
        pass
