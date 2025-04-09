from dns import DNS_ADDR
from process import runcmd
from process import run as process_run
import shlex
import os
import glob


def run(topo, website, result_dir):
    # start our container and add to the topology
    dflags = f"--rm -it -d --dns {DNS_ADDR} --network=none --name lighthouse-{topo.nsid}"
    process_run(shlex.split(f"docker run {dflags} scouture/lighthouse /bin/bash"))
    pid = runcmd(f"docker inspect -f {{{{.State.Pid}}}} lighthouse-{topo.nsid}")
    pid = pid.stdout.decode("utf-8").strip()

    # link the namespace
    runcmd("mkdir -p /var/run/netns")
    runcmd(f"ln -s /proc/{pid}/ns/net /var/run/netns/lighthouse-{topo.nsid}")

    # add to the topology
    topo.attach_client_with_ip(f"lighthouse-{topo.nsid}", "10.0.1.63")

    # make our rundir and copy the script over
    runcmd(f"docker exec lighthouse-{topo.nsid} mkdir -p /lighthouse/")
    run_script = os.path.abspath("lighthouse/run-lighthouse.sh")
    runcmd(f"docker cp {run_script} lighthouse-{topo.nsid}:/")

    dflags = (
        "-w /lighthouse/"
    )

    # run the client then copy the files over to the destination dir
    dockercmd = f"docker exec {dflags} lighthouse-{topo.nsid} sh -- /run-lighthouse.sh {website}"
    p = runcmd(dockercmd, exceptionok=True)
    print(f"lighthouse stdout:\n{p.stdout.decode('utf-8').strip()}\nlighthouse stderr:\n{p.stderr.decode('utf-8').strip()}")

    # copy the results over
    result_dir = os.path.abspath(result_dir)
    os.makedirs(result_dir, exist_ok=True)
    runcmd(f"docker cp lighthouse-{topo.nsid}:/lighthouse/. {result_dir}")

    # stop the container and remove the namespace link
    runcmd(f"docker kill lighthouse-{topo.nsid}")
    runcmd(f"rm /var/run/netns/lighthouse-{topo.nsid}")


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
