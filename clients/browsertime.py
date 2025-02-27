from dns import DNS_ADDR
from process import runcmd
from process import run as process_run
from eval.hol import hol_compute
import shlex
import os
import glob
import json


def run(topo, website, result_dir):
    # start our container and add to the topology
    dflags = f"--rm -it -d --dns {DNS_ADDR} --network=none --name browsertime-{topo.nsid}"
    runcmd(f"docker run {dflags} scouture/browsertime /bin/bash")
    pid = runcmd(f"docker inspect -f {{{{.State.Pid}}}} browsertime-{topo.nsid}")
    pid = pid.stdout.decode("utf-8").strip()
    # link the namespace
    runcmd("mkdir -p /var/run/netns")
    runcmd(f"ln -s /proc/{pid}/ns/net /var/run/netns/browsertime-{topo.nsid}")
    # add to the topology
    topo.attach_client_with_ip(f"browsertime-{topo.nsid}", "10.0.1.83")

    dflags = (
        "-w /browsertime/"
    )

    btflags = (
        "--resultDir /browsertime/ "
        "--chrome.args \"disable-field-trial-config\" "
        "--xvfb true "
        "--chrome.args \"ignore-privacy-mode\" "
        "--chrome.args \"enable-quic\" "
        "--chrome.args \"quic-version=h3\" "
        "--chrome.args \"origin-to-force-quic-on=*\" "
        "--chrome.collectNetLog true "
        "--timeouts.pageCompleteCheck 300000 "
        "--timeouts.pageLoad 300000 "
        "--visualMetrics "
        "-n 1 "
        "--videoParams.framerate 50 "
        "--videoParams.createFilmstrip false "
        "--useSameDir true"
    )

    # run the client then copy the files over to the destination dir
    # split it up like this so the flags correctly go to browsertime (and not node)
    dockercmd = f"docker exec {dflags} browsertime-{topo.nsid} node -- /usr/src/app/bin/browsertime.js {btflags} https://{website}"
    p = process_run(shlex.split(dockercmd))
    print(f"browsertime stdout:\n{p.stdout.decode('utf-8').strip()}\nbrowsertime stderr:\n{p.stderr.decode('utf-8').strip()}")

    # copy the results over
    result_dir = os.path.abspath(result_dir)
    os.makedirs(result_dir, exist_ok=True)
    runcmd(f"docker cp browsertime-{topo.nsid}:/browsertime/. {result_dir}")

    # compute our metrics
    metrics = compute_metrics(result_dir)

    # stop the container and remove the namespace link
    runcmd(f"docker kill browsertime-{topo.nsid}")
    runcmd(f"rm /var/run/netns/browsertime-{topo.nsid}")

    # return the metrics
    return metrics


# create a dictionry of metrics - mostly browsertime-provided but some custom
def compute_metrics(result_dir):
    # use the hol_compute script
    netlog_pattern = os.path.join(result_dir, "chromeNetlog*json*")
    matches = glob.glob(netlog_pattern)
    netlog = matches[0] if matches else None
    # if we couldn't find the netlog, say so and return empty results
    if not netlog:
        print(f"unable to find netlog in dir {result_dir}, no hol metrics")
        hol_data = {}
    else:
        hol_data = hol_compute(netlog)

    btjson = os.path.join(result_dir, "browsertime.json")
    try:
        with open(btjson) as f:
            btdata = json.load(f)
        metrics = btdata[0]["visualMetrics"][0]
        copymetrics = {
            "FirstVisualChange": "fvc",
            "LastVisualChange": "lvc",
            "SpeedIndex": "si",
            "VisualComplete85": "vc85",
            "VisualComplete95": "vc95",
            "VisualComplete99": "vc99",
        }

        btmetrics = {to: metrics[from_] for from_, to in copymetrics.items()}
        btmetrics["plt"] = btdata[0]["statistics"]["timings"]["pageTimings"]["pageLoadTime"]["median"]
        btmetrics["runtime"] = btdata[0]["timestamps"][0]

    except Exception as e:
        print(f"problem openening {btjson}: {e}")
        btmetrics = {}

    metrics = hol_data | btmetrics
    return metrics
