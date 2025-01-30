from dns import DNS_ADDR
from process import runcmd
from process import run as process_run
import shlex
import os


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
    p = runcmd(dockercmd)
    print(f"lighthouse stdout:\n{p.stdout.decode('utf-8').strip()}\nlighthouse stderr:\n{p.stderr.decode('utf-8').strip()}")

    # copy the results over
    result_dir = os.path.abspath(result_dir)
    os.makedirs(result_dir, exist_ok=True)
    runcmd(f"docker cp lighthouse-{topo.nsid}:/lighthouse/. {result_dir}")

    # stop the container and remove the namespace link
    runcmd(f"docker kill lighthouse-{topo.nsid}")
    runcmd(f"rm /var/run/netns/lighthouse-{topo.nsid}")
