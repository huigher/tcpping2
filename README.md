# 脚本主要功能和示例
1. 连接指定的目标和端口
2. 指定本地源IP和源端口连接指定目标IP和端口
3. 支持以FIN和RESET方式断开连接
4. 默认情况下和linux下的ping类似，会持续的进行连接，可以通过`-c`参数来制定连接的次数
5. 同步输出日志文件，方便关闭程序后查看历史连接情况
6. 还支持一些额外的参数，如`-i`可以调节连接的间隔

# 脚本会做的事情
1. 以给定的参数构建五元组，使用TCP去连接目标
2. 记录连接时间，打印在标准输出上，同时记录到同名的日志文件中
3. 循环执行，或者在执行COUNT（给定参数）次退出
4. 在收到TERM或INT信号后强制结束，同时输出此次运行的统计结果

# 命令示例
## 连接指定8.8.8.8的53端口
`python tcpping2.py 8.8.8.8 53`

## 指定本地源地址和源端口10086去连接8.8.8.8的53端口
`python tcpping2.py -H 30.11.212.23 -P 10086 8.8.8.8 53`

## 指定连接10次目标地址
`python tcpping2.py -c 10 8.8.8.8 53`

## 以RESET断开连接
`python tcpping2.py -R 8.8.8.8 53`

## 间隔1秒进行一次探测
`python tcpping2.py -i 1 8.8.8.8 53`

## 查看帮助
`python tcpping2.py -h`

# usage

```
usage: tcpping2 [-h] [-H SRC_HOST] [-P SRC_PORT] [-L SRC_ROTATE_PORT]
                [-i INTERVAL] [-t TIMEOUT] [-c COUNT] [-R]
                dst_host dst_port

A tiny tool to connect target using TCP Connection. Version:0.1.0

positional arguments:
  dst_host
  dst_port

optional arguments:
  -h, --help            show this help message and exit
  -H SRC_HOST, --src-host SRC_HOST
                        set local IP
  -P SRC_PORT, --src-port SRC_PORT
                        set local port
  -L SRC_ROTATE_PORT, --src-rotate-port SRC_ROTATE_PORT
                        set local port(rotate)
  -i INTERVAL, --interval INTERVAL
                        set connection interval(second)
  -t TIMEOUT, --timeout TIMEOUT
                        set timeout(second)
  -c COUNT, --count COUNT
                        Stop after sending count packets
  -R, --rst             Sending reset packet to close connection instead of
                        FIN

examples: tcpping2.py 192.168.1.25 80
```

# github
https://github.com/huigher/tcpping2

# 最后
脚本编写仓促，难免会有bug或不妥的地方，各位如有建议、吐槽，欢迎联系我：）