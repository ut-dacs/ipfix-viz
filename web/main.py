from flask import Flask, render_template, g, request
import rrdtool
import configparser
from os.path import basename
import os

app = Flask(__name__)
config = configparser.ConfigParser()


base_dir =  os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))
print(base_dir)
config.read(os.path.join(base_dir, 'config.conf'))


#config.read('config.conf')


RRD_DIR     = os.path.join(base_dir, "")  #"ipfix-rrd")
GRAPH_DIR   = os.path.join(base_dir, "web/static")


def before_first_request():
    pass


@app.route('/')
def dashboard():
    rrd_files = ["{}/{}.rrd".format(RRD_DIR, r) for r in config.sections()]
    print(rrd_files)
    graph_files = []
    #args_start = "--start"
    #args_end = "end-2D"
    args_time = request.args.get('time', '2D')
    #if request.args['time']:
    #    args_time = request.args['time']

    graph_args = ["--end", "now", "--start", "end-{}".format(args_time), "--width", config['DEFAULT']['plot_width']]
    for rrd_file in rrd_files:
        graph_file = "{}/{}.png".format("static", basename(rrd_file))
        graph_args_flows    = graph_args + ["DEF:flows={}:flows:AVERAGE".format(rrd_file), "LINE1:flows#0000ff:{} flows".format(basename(rrd_file))]
        graph_args_packets  = graph_args + ["DEF:packets={}:packets:AVERAGE".format(rrd_file), "LINE1:packets#ff00ff:{} packets".format(basename(rrd_file))]
        graph_args_bytes    = graph_args + ["DEF:bytes={}:bytes:AVERAGE".format(rrd_file), "LINE1:bytes#00ffff:{} bytes".format(basename(rrd_file))]
        graph_file_flows = "{}/{}_flows.png".format("static", basename(rrd_file))
        graph_file_packets = "{}/{}_packets.png".format("static", basename(rrd_file))
        graph_file_bytes = "{}/{}_bytes.png".format("static", basename(rrd_file))
        rrdtool.graph(graph_file_flows, graph_args_flows)
        rrdtool.graph(graph_file_packets, graph_args_packets)
        rrdtool.graph(graph_file_bytes, graph_args_bytes)

        graph_files.append(graph_file_flows)
        graph_files.append(graph_file_packets)
        graph_files.append(graph_file_bytes)

        # rrdtool.graph(graph_file, 
        #                 "--end",    "now",
        #                 "--start",  "end-2d",
        #                 "--width",  "300",
        #                 "DEF:flows={}:flows:AVERAGE".format(rrd_file),
        #                 "LINE1:flows#0000ff:{} flows".format(basename(rrd_file)))

    return render_template('dashboard.html', graph_files=graph_files)

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r
