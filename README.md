# OpenTSDB + Grafana

This setup requires OpenTSDB, which in turn requires Hbase, and Grafana.
Instructions provided are for a Debian-based system.

## OpenTSDB + Hbase

First, set up Hbase according to https://hbase.apache.org/book.html#quickstart

Start it with
```
JAVA_HOME=/usr ./bin/start-hbase.sh
```

Then, get an OpenTSDB release from https://github.com/OpenTSDB/opentsdb/releases

Create the necessary tables via e.g.
```
env COMPRESSION=NONE HBASE_HOME=/home/hendriksl/hbase-1.2.6 /usr/share/opentsdb/tools/create_table.sh
```

and start the `opentsdb` service.

## Grafana

Get the latest release from http://docs.grafana.org/installation/debian/ ,
install and start the `grafana-server` service.

## Cronjob to insert new datapoints from collected flow data

The script called `fbit_to_rrd.py` updates both the RRD files as well as the opentsdb database.
An example cronjob to update every 5 minutes:

```bash
2,7,12,17,22,27,32,37,42,47,52,57 * * * * cd /home/hendriksl/ipfix-rrd && python3 /home/hendriksl/ipfix-rrd/fbit_to_rrd.py auto > /dev/null
```

## Connect Grafana and OpenTSDB

In the Grafana web-interface, click on the Grafana logo in the upper left
corner and choose 'Data sources' from the dropdown menu.  Click 'Add data
source'. Set 'Type' to 'OpenTSDB' and configure the URL to be
http://localhost:4242 and set 'Access' to 'Proxy'. Further configuration might
depend on specific versions of OpenTSDB used.

Now, new dashboards with custom plots can be created via 'Dashboards' in the
dropdown menu, where the datapoints from the OpenTSDB database should appear
when defining a new graph.


# ipfix-rrd: RRD based graphing

## Installation / Configuration

```
apt install librrd-dev libpython3-dev
```

### create a virtualenv

```bash
sudo apt install python3-venv
python3 -m venv my_venv
source ./venv/bin/activate
```

### pip dependencies

```bash
pip install --upgrade pip
pip install rrdtool flask
```

### Web ui

* activate venv
* `FLASK_APP=main.py flask run`


## Update RRD files via cron
```bash
2,7,12,17,22,27,32,37,42,47,52,57 * * * * cd /home/hendriksl/ipfix-rrd && python3 /home/hendriksl/ipfix-rrd/fbit_to_rrd.py auto > /dev/null
```
