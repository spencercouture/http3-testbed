from process import run
import os
import shutil
from process import runcmd

DNS_ADDR = "10.0.1.4"


# start dnsmasq for the hostnames in a given topo
def start_dnsmasq(topo, hostnames, resolve_addr):
    # stop it first
    stop_dnsmasq(topo)
    # make our dir
    path = os.path.abspath(f"dns/{topo.nsid}")
    os.makedirs(path, exist_ok=True)

    # populates hosts file
    hosts_filename = path + "/hosts"
    hosts = "\n".join([resolve_addr + " " + hostname for hostname in hostnames]) + "\n"
    with open(hosts_filename, "w") as f:
        f.write(hosts)

    # populates config file
    config_filename = path + "/conf"
    config = "log-queries"
    with open(config_filename, "w") as f:
        f.write(config)

    args = ["dnsmasq", "-u", "root", "--no-resolv", "--no-hosts", "-C", config_filename, "-H", hosts_filename, "-x", f"{path}/dnsmasq.pid"]
    p = run(args, topo.client_ns)
    return p


# kills dnsmasq for a given topo/nsid
def stop_dnsmasq(topo):
    pid_file = os.path.abspath(f"dns/{topo.nsid}/dnsmasq.pid")
    if not os.path.exists(pid_file):
        return False

    pid = runcmd(f"cat {pid_file}").stdout.decode("utf-8").strip()

    runcmd(f"kill -9 {pid}", exceptionok=True)
    os.remove(pid_file)
