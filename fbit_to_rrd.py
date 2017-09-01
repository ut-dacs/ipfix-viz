#!/usr/bin/env python3

import sys
import datetime as dt
import subprocess
import shlex

import asyncio
import rrdtool
import os

import configparser
config = configparser.ConfigParser()


base_dir =  os.path.dirname(os.path.realpath(__file__))
config.read(os.path.join(base_dir, 'config.conf'))


@asyncio.coroutine
def process_query(fbit_dir, fbit_query_name):
    dir_date = fbit_dir[-14:]
    unix_ts = dt.datetime.strptime(dir_date, "%Y%m%d%H%M%S").strftime("%s")

    query_cmd = "{} -C {} -R {} -A -N10 -q -o'{}' '{}'".format(
        config['DEFAULT']['fbitdump_bin'],
        config['DEFAULT']['fbitdump_config'],
        fbit_dir,
        config[fbit_query_name]['query_output'],
        config[fbit_query_name]['query_filter']
        )

    sub = asyncio.create_subprocess_exec(*shlex.split(query_cmd), stdout=asyncio.subprocess.PIPE);
    proc = yield from sub
    data = yield from proc.stdout.readline()
    line = data.decode('ascii').rstrip()
    #print(fbit_query.get('name'), line)
    if line:
        pkt, byt, fl = [x.strip() for x in line.split(':')]
        rrdtool.update("{}.rrd".format(fbit_query_name), "{}:{}:{}:{}".format(unix_ts, fl, pkt, byt))
    yield from proc.wait()
 

@asyncio.coroutine
def main(loop, fbit_dir):
    coroutines = [process_query(fbit_dir, fbit_query_name) for fbit_query_name in config.sections()]
    for coroutine in asyncio.as_completed(coroutines):
        yield from coroutine
 
def create_rrds():
    for q in config.sections():
        rrdfile = "{}.rrd".format(q)
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
