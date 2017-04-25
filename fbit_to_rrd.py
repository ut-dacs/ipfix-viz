#!/usr/bin/env python3

import sys
import datetime as dt
import subprocess
import shlex

import asyncio
import rrdtool
import os.path

queries = [
{"name": "all",  "query" : "/usr/local/bin/fbitdump -C /home/hendriksl/fbitdump.xml -R {} -A  -N 10 -q -o'fmt:%pkt:%byt:%fl'", "rrd_format" : "TODO"} ,
{"name": "tcp",  "query" : "/usr/local/bin/fbitdump -C /home/hendriksl/fbitdump.xml -R {} -A  -N 10 -q -o'fmt:%pkt:%byt:%fl' '%proto TCP'", "rrd_format" : "TODO"} ,
{"name": "udp",  "query" : "/usr/local/bin/fbitdump -C /home/hendriksl/fbitdump.xml -R {} -A  -N 10 -q -o'fmt:%pkt:%byt:%fl' '%proto UDP'", "rrd_format" : "TODO"} ,
{"name": "icmp6",  "query" : "/usr/local/bin/fbitdump -C /home/hendriksl/fbitdump.xml -R {} -A  -N 10 -q -o'fmt:%pkt:%byt:%fl' '%proto IPv6-ICMP'", "rrd_format" : "TODO"} ,
{"name": "frag6",  "query" : "/usr/local/bin/fbitdump -C /home/hendriksl/fbitdump.xml -R {} -A  -N 10 -q -o'fmt:%pkt:%byt:%fl' '%proto IPv6-FRAG'", "rrd_format" : "TODO"},
{"name": "ehCnt1",  "query" : "/usr/local/bin/fbitdump -C /home/hendriksl/fbitdump.xml -R {} -A  -N 10 -q -o'fmt:%pkt:%byt:%fl' '%v6ehCnt 1'", "rrd_format" : "TODO"} ,
{"name": "ehCnt2",  "query" : "/usr/local/bin/fbitdump -C /home/hendriksl/fbitdump.xml -R {} -A  -N 10 -q -o'fmt:%pkt:%byt:%fl' '%v6ehCnt 2'", "rrd_format" : "TODO"} ,
{"name": "ehCntgt2",  "query" : "/usr/local/bin/fbitdump -C /home/hendriksl/fbitdump.xml -R {} -A  -N 10 -q -o'fmt:%pkt:%byt:%fl' '%v6ehCnt > 2'", "rrd_format" : "TODO"} ,
{"name": "upperTcp",  "query" : "/usr/local/bin/fbitdump -C /home/hendriksl/fbitdump.xml -R {} -A  -N 10 -q -o'fmt:%pkt:%byt:%fl' '%v6ehCnt > 0 and %v6ehUpperProto TCP'", "rrd_format" : "TODO"},
{"name": "upperUdp",  "query" : "/usr/local/bin/fbitdump -C /home/hendriksl/fbitdump.xml -R {} -A  -N 10 -q -o'fmt:%pkt:%byt:%fl' '%v6ehCnt > 0 and %v6ehUpperProto UDP'", "rrd_format" : "TODO"},
{"name": "upperIcmp6",  "query" : "/usr/local/bin/fbitdump -C /home/hendriksl/fbitdump.xml -R {} -A  -N 10 -q -o'fmt:%pkt:%byt:%fl' '%v6ehCnt > 0 and %v6ehUpperProto IPv6-ICMP'", "rrd_format" : "TODO"},
{"name": "upperIpsecEsp",  "query" : "/usr/local/bin/fbitdump -C /home/hendriksl/fbitdump.xml -R {} -A  -N 10 -q -o'fmt:%pkt:%byt:%fl' '%v6ehCnt > 0 and %v6ehUpperProto IPSEC-ESP'", "rrd_format" : "TODO"},
]

@asyncio.coroutine
def process_query(fbit_dir, fbit_query):
    dir_date = fbit_dir[-14:]
    unix_ts = dt.datetime.strptime(dir_date, "%Y%m%d%H%M%S").strftime("%s")
    sub = asyncio.create_subprocess_exec(*shlex.split(fbit_query.get('query').format(fbit_dir)), stdout=asyncio.subprocess.PIPE);
    proc = yield from sub
    data = yield from proc.stdout.readline()
    line = data.decode('ascii').rstrip()
    #print(fbit_query.get('name'), line)
    if line:
        pkt, byt, fl = [x.strip() for x in line.split(':')]
        rrdtool.update("{}.rrd".format(fbit_query.get('name')), "{}:{}:{}:{}".format(unix_ts, fl, pkt, byt))
    yield from proc.wait()
 

@asyncio.coroutine
def main(loop, fbit_dir):
    coroutines = [process_query(fbit_dir, fbit_query) for fbit_query in queries]
    for coroutine in asyncio.as_completed(coroutines):
        yield from coroutine
 
def create_rrds():
    for q in queries:
        rrdfile = "{}.rrd".format(q['name'])
        if not os.path.isfile(rrdfile):
            print("Missing {}, creating it".format(rrdfile))
            rrdtool.create(rrdfile,
                "--start",      "now - 10d",
                "--step",       "300s",
                "DS:flows:GAUGE:300:0:U",
                "DS:packets:GAUGE:300:0:U",
                "DS:bytes:GAUGE:300:0:U",
                "RRA:AVERAGE:0.5:1:105120") # 105120 == 12 * 24 * 365 == 1 year of 5min datapoints

def find_last_fbit_dir():
    five_min_ago = dt.datetime.now() - dt.timedelta(minutes=5)
    previous_timestamp = five_min_ago.replace(minute=5*(five_min_ago.minute // 5))
    return previous_timestamp.strftime("/mnt/data/fbit_ipfix/4/%Y/%m/%d/ic%Y%m%d%H%M00")

 
if __name__ == '__main__':

    create_rrds()

    if len(sys.argv) != 2:
        print("need argument, aborting...", file=sys.stderr)
        exit(1)

    fbit_dir = sys.argv[1]
    if fbit_dir == "auto":
        print("Trying to find last but one fbit dir on my own...")
        fbit_dir = find_last_fbit_dir()
        if not fbit_dir:
            print("Could not determine last but one fbit dir, aborting...", file=sys.stderr)
            exit(2)
        else:
            print("Got ", fbit_dir)
            #exit(0)
    elif not os.path.isdir(fbit_dir):
        print("input dir does not exist aborting...", file=sys.stderr)
        exit(1)


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop, fbit_dir))
    loop.close()
