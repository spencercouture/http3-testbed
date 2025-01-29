from dns import DNS_ADDR
from process import runcmd
from process import run as process_run
import shlex
import os


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

    # stop the container and remove the namespace link
    runcmd(f"docker kill browsertime-{topo.nsid}")
    runcmd(f"rm /var/run/netns/browsertime-{topo.nsid}")
