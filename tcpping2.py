#!/usr/bin/python
# encoding: utf-8

import argparse
import time
import socket
import struct
import logging
from datetime import datetime

__VERSION__ = '0.1.0'


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
        logging.error(tip)
        return False
    else:
        return True


def go(dst_host, dst_port, timeout, interval, src_host=None, src_port=None, count=None, src_rotate_port=None, rst=False,
       ):
    error_flag = False
    if src_rotate_port:
        src_port = src_rotate_port

    while judge_count(count):
        (conn_time, close_time, err, local_addr) = conn_tcp(dst_host, dst_port, timeout=timeout, src_host=src_host,
                                                            src_port=src_port, rst=rst)
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
        print final_output
        if error_flag:
            logging.error(final_output)
        else:
            logging.info(final_output)

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
            logging.warning(tip_reach_65535)
            src_port = 1024

        # 若有 count，自减1
        if count is not None:
            count -= 1

        # 连接间隔
        time.sleep(interval)


def initial(arguments):
    # 开启log记录
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)s: %(asctime)s - %(filename)s[line:%(lineno)d] -  %(message)s',
                        filename='tcpping2_' + arguments.dst_host[0] + '_' + str(arguments.dst_port[0]) + '.log',
                        filemode='w')


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
    parser.add_argument('-H', '--src-host', dest='src_host', help='set local IP', type=str)
    # 本地源端口
    parser.add_argument('-P', '--src-port', dest='src_port', help="set local port", type=int)
    # 本地源端口，自增的进行连接，一般用来地毯式的查找本地有问题的源端口
    parser.add_argument('-L', '--src-rotate-port', dest='src_rotate_port', help="set local port(rotate)", type=int)
    # 连接间隔
    parser.add_argument('-i', '--interval', dest='interval', help="set connection interval(second)", type=float)
    # 连接超时时间
    parser.add_argument('-t', '--timeout', dest='timeout', help="set timeout(second)", type=float)
    # 总的连接次数
    parser.add_argument('-c', '--count', dest='count', help="Stop after sending count packets", type=int)
    # 是否以RESET断开连接，可以加快两端的系统回收连接
    parser.add_argument('-R', '--rst', dest='rst', action='store_true',
                        help="Sending reset packet to close connection instead of FIN")
    # 连接的目标主机
    parser.add_argument('dst_host', nargs=1, action='store')
    # 连接的目标端口
    parser.add_argument('dst_port', nargs=1, action="store", type=int)

    return parser.parse_args()


if __name__ == '__main__':
    args = getargs()
    initial(args)
    if judge_args(args):
        go(args.dst_host[0], args.dst_port[0], timeout=args.timeout if args.timeout else 10,
           interval=args.interval if args.interval else 3,
           src_host=args.src_host if args.src_host else None, src_port=args.src_port if args.src_port else 0,
           src_rotate_port=args.src_rotate_port if args.src_rotate_port else None, rst=args.rst if args.rst else None,
           count=args.count if args.count else None)
    else:
        pass
