# ipfix-rrd

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
