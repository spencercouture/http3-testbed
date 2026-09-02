# quiche.py
from process import runcmd, run
import os
from dns import DNS_ADDR
from mitmproxy.mitmproxy import get_protobuf_path


# starts quiche (assumes the topo is up)
def start(topo, website, addr, port, cert_dir):
    cert_file = os.path.join(cert_dir, "cert.crt")
    key_file = os.path.join(cert_dir, "cert.key")

    # setup our flags and starts the container
    proto_path = get_protobuf_path(website)
    dflags = f"--rm -it -d -v {proto_path}:/protobuf_files -v {cert_dir}:/certs --dns {DNS_ADDR} --network=none --name quiche-server-{topo.nsid}"
    runcmd(f"docker run {dflags} scouture/protobuf-quiche-noprio /bin/bash")
    pid = runcmd(f"docker inspect -f {{{{.State.Pid}}}} quiche-server-{topo.nsid}")
    pid = pid.stdout.decode("utf-8").strip()
    runcmd(f"docker exec -d quiche-server-{topo.nsid} mkdir -p /quiche/")

    # link the namespace
    runcmd("mkdir -p /var/run/netns")
    runcmd(f"ln -sf /proc/{pid}/ns/net /var/run/netns/quiche-server-{topo.nsid}")

    # add to the topology
    topo.attach_server_with_ip(f"quiche-server-{topo.nsid}", addr)

    # start quiche
    d_flags = (
        "-e QLOGDIR=/quiche/ "
        "-e RUST_BACKTRACE=1 "
        "-e SSLKEYLOGFILE=/quiche/sslkeyfile "
        "-w /quiche/"
    )
    quiche_flags = (
        f"--listen {addr}:{port} "
        f"--cert /certs/cert.crt "
        f"--key /certs/cert.key"
    )

    # first run iperf3
    dockercmds = f"docker exec -d {d_flags} quiche-server-{topo.nsid}".split(" ")
    iperfcmds = ["bash", "-c", "iperf3 -s 2>&1 | tee /quiche/iperf3.log"]
    run(dockercmds + iperfcmds)

    # capture tc qdisc state, place alongside other quiche logs
    qdisc = runcmd("tc -s qdisc show", namespace=f"{topo.nsid}-ns0", exceptionok=True)
    qdisc_tmp = f"/tmp/qdisc-{topo.nsid}.log"
    with open(qdisc_tmp, "w") as f:
        f.write(qdisc.stdout.decode("utf-8") + qdisc.stderr.decode("utf-8"))
    runcmd(f"docker cp {qdisc_tmp} quiche-server-{topo.nsid}:/quiche/qdisc.log")
    os.remove(qdisc_tmp)

    # we split it up like this so we can use tee inside the docker cmd, and handle server output that way
    dockercmds = f"docker exec -d {d_flags} quiche-server-{topo.nsid}".split(" ")
    quichecmds = ["bash", "-c", f"quiche-server {quiche_flags} 2>&1 | tee /quiche/server.log"]
    run(dockercmds + quichecmds)


def stop(topo):
    # stop the container
    runcmd(f"docker kill quiche-server-{topo.nsid}")
    # remove the namespace link
    runcmd(f"rm /var/run/netns/quiche-server-{topo.nsid}")


def copy_files(topo, dest):
    runcmd(f"docker cp quiche-server-{topo.nsid}:/quiche/. {dest}")
