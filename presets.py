from topology import Topology
from certs.certs import create_certs
from mitmproxy.mitmproxy import get_hostnames, capture_site
from dns import start_dnsmasq
from servers import quiche
from clients import browsertime, lighthouse
import os


# the dictionary of name->functions to choose from CLI
PRESETS = {}


def register_preset(name):
    def wrapper(func):
        PRESETS[name] = func
        return func
    return wrapper


@register_preset("full_quiche_run")
def full_quiche_run(result_dir):
    quiche_addr = "10.0.9.83"
    # run full testbed for each of the sites
    # sites = [("www.npr.org", "npr"), ("www.bbc.com", "bbc"), ("www.bestbuy.com", "bbuy"), ("www.homedepot.org", "hdepo")]
    sites = [
        ("www.wikipedia.org", "wiki"),
        ("www.nytimes.com", "nytim"),
        ("www.bbc.com", "bbc"),
        ("www.reddit.com", "redit"),
        ("www.cnn.com", "cnn"),
        ("www.espn.com", "espn"),
        ("www.github.com", "gthub"),
        ("www.stackoverflow.com", "stovf"),
        ("www.medium.com", "medum"),
        ("www.bloomberg.com", "blmbg"),
        ("www.nationalgeographic.com", "natgeo"),
        ("www.imdb.com", "imdb"),
        ("www.apple.com", "apple"),
        ("www.microsoft.com", "msft"),
        ("www.craigslist.org", "crgls"),
        ("www.target.com", "targt"),
        ("www.walmart.com", "wlmrt"),
        ("www.bestbuy.com", "bstby"),
        ("www.tripadvisor.com", "tripd"),
        ("www.weather.com", "weath"),
        ("www.theguardian.com", "grdn"),
        ("www.aljazeera.com", "aljaz"),
        ("www.forbes.com", "forbs"),
        ("www.usatoday.com", "usatd"),
        ("www.theverge.com", "verge"),
        ("www.techcrunch.com", "tcrch"),
        ("www.engadget.com", "engdt"),
        ("www.fandom.com", "fndom"),
        ("www.soundcloud.com", "sndcl"),
        ("www.spotify.com", "spoti"),
        ("www.youtube.com", "ytube"),
        ("www.vimeo.com", "vimeo"),
        ("www.netflix.com", "ntflx"),
        ("www.hulu.com", "hulu"),
        ("www.disneyplus.com", "dplus"),
        ("www.booking.com", "bookg"),
        ("www.airbnb.com", "airbb"),
        ("www.kayak.com", "kayak"),
        ("www.lonelyplanet.com", "lnpln"),
        ("www.allrecipes.com", "alrcp"),
        ("www.foodnetwork.com", "fdnet"),
        ("www.webmd.com", "webmd"),
        ("www.mayoclinic.org", "mayo"),
        ("www.healthline.com", "hltln"),
        ("www.khanacademy.org", "khan"),
        ("www.coursera.org", "crsra"),
        ("www.edx.org", "edx"),
        ("www.quora.com", "quora"),
        ("www.archive.org", "archv"),
        ("www.irs.gov", "irs"),
        ("www.loc.gov", "loc"),
    ]
    fails = []
    for (site, nsid) in sites:
        # capture the site. (if not already present)
        capture_site(site, overwrite=True)
        site_res_dir = os.path.join(result_dir, site)
        if os.path.isdir(site_res_dir):
            print(f"error: {site_res_dir} exists. skipping {site}...")
            continue

        # first bring the topo up
        topo = Topology(nsid)
        topo.up()

        # get certs and DNS configured
        hostnames = get_hostnames(site)
        cert_dir = create_certs(hostnames)
        start_dnsmasq(topo, hostnames, quiche_addr)

        # start quiche
        quiche.start(topo, site, quiche_addr, 443, cert_dir)

        # run browsertime
        print("running browsertime...")
        try:
            btpath = os.path.join(site_res_dir, "browsertime")
            btstats = browsertime.run(topo, site, btpath)
        except Exception as e:
            print(f"error running browsertime for {site}")
            fails.append(f"{site} (browsertime) {e}")

        # run lighthouse
        print("running lighthouse...")
        try:
            lhpath = os.path.join(site_res_dir, "lighthouse")
            lhstats = lighthouse.run(topo, site, lhpath)
        except Exception as e:
            print(f"error running lighthouse for {site}")
            fails.append(f"{site} (lighthouse) {e}")

        # copy server files
        try:
            quiche_path = os.path.join(site_res_dir, "quiche")
            quiche.copy_files(topo, quiche_path)
        except Exception as e:
            print(f"error copying quiche files to {quiche_path}")
            fails.append(f"{site} (quiche - copy) {e}")

        # and stop quiche
        try:
            quiche.stop(topo)
        except Exception as e:
            print(f"error stopping quiche")
            fails.append(f"{site} (quiche - stop) {e}")

        # remove topology and added server ns
        topo.teardown()

    # log fails at the end if any
    if fails:
        print(f"FAILURES found during the following:")
        for fail in fails:
            print(f"\t{fail}")

