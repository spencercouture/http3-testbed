from topology import Topology
from certs.certs import create_certs
from mitmproxy.mitmproxy import get_hostnames, capture_site
from dns import start_dnsmasq
from servers import quiche
from clients import browsertime, lighthouse
import os
import json
import time
import logging


# the dictionary of name->functions to choose from CLI
PRESETS = {}


def register_preset(name):
    def wrapper(func):
        PRESETS[name] = func
        return func
    return wrapper


@register_preset("full_quiche_run")
def full_quiche_run(result_dir):
    impairements = [
        # --- bandwidth sweep: 20ms RTT, no loss (throughput is link-limited) ---
        {
            "bw":  1000,
            "rtt": 20,
            "bdp": 1,
            "loss": 0
        },  # ~1000 Mbps   gigabit fiber
        {
            "bw":  500,
            "rtt": 20,
            "bdp": 1,
            "loss": 0
        },  # ~500 Mbps    fiber / fast cable
        # {
        #     "bw":  250,
        #     "rtt": 20,
        #     "bdp": 1,
        #     "loss": 0
        # },  # ~250 Mbps    cable / strong 5G
        {
            "bw":  100,
            "rtt": 20,
            "bdp": 1,
            "loss": 0
        },  # ~100 Mbps    baseline broadband
        {
            "bw":  50,
            "rtt": 20,
            "bdp": 1,
            "loss": 0
        }  # ~50 Mbps     entry broadband / good LTE
        # {
        #     "bw":  10,
        #     "rtt": 20,
        #     "bdp": 1,
        #     "loss": 0
        # },  # ~10 Mbps     weak link, kept as prior-work anchor
        #
        # # --- RTT sweep at 100 Mbps, no loss (throughput ~flat; this drives page-load time) ---
        # {
        #     "bw":  100,
        #     "rtt": 10,
        #     "bdp": 1,
        #     "loss": 0
        # },  # ~100 Mbps    same-region fiber
        # {
        #     "bw":  100,
        #     "rtt": 100,
        #     "bdp": 1,
        #     "loss": 0
        # },  # ~100 Mbps    transcontinental / mobile
        #
        # # --- random loss at 100 Mbps / 40ms (loss-based CC capped well under link rate) ---
        # {
        #     "bw":  100,
        #     "rtt": 40,
        #     "bdp": 1,
        #     "loss": 0.005
        # },  # ~5 Mbps      CUBIC-limited (BBR ~near link)
        # {
        #     "bw":  100,
        #     "rtt": 40,
        #     "bdp": 1,
        #     "loss": 0.01
        # },  # ~3.5 Mbps    CUBIC-limited (BBR ~near link)
        # {
        #     "bw":  100,
        #     "rtt": 40,
        #     "bdp": 1,
        #     "loss": 0.02
        # },  # ~2.5 Mbps    CUBIC-limited (BBR ~near link)
        #
        # # --- high link + loss: proves the CUBIC ceiling is loss-bound, not link-bound ---
        # {
        #     "bw":  500,
        #     "rtt": 40,
        #     "bdp": 1,
        #     "loss": 0.01
        # }   # ~3.5 Mbps    CUBIC (same as the 100 Mbps row above!)
    ]
    quiche_addr = "10.0.9.83"
    # run full testbed for each of the sites
    # sites = [("www.npr.org", "npr"), ("www.bbc.com", "bbc"), ("www.bestbuy.com", "bbuy"), ("www.homedepot.org", "hdepo")]
    sites = [
        # Search & Technology
        # ("www.nike.com", "nikexx"),
        # ("www.nytimes.com", "nytimes"),
        # ("www.homedepot.com", "hmdpot"),
        # ("www.costco.com", "costco")
        # ("www.zillow.com", "zillow"),
        #
        # # News & Information
        #
        ("www.npr.org", "nprxxx"),
        # ("www.bbc.com", "bbcnew"),
        # ("www.cnn.com", "cnnnew"),
        # ("www.reuters.com", "reutrs"),
        # ("www.wsj.com", "wsjnew"),
        # ("www.bloomberg.com", "blmbgx"),
        # ("www.ft.com", "fintms"),
        # ("www.cnbc.com", "cnbcxx"),
        # ("www.foxnews.com", "foxnws"),
        # ("www.huffpost.com", "huffpt"),
        # ("www.wired.com", "wiredx"),
        # ("www.gizmodo.com", "gizmod"),
        #
        # # Business, Finance & Cryptocurrencies
        # ("www.paypal.com", "paypal"),
        # ("www.stripe.com", "stripex"),
        # ("www.chase.com", "chasex"),
        # ("www.bankofamerica.com", "bofamx"),
        # ("www.coinbase.com", "coinbs"),
        # ("www.binance.com", "binanc"),
        # ("www.investopedia.com", "invpda"),
        # ("www.fidelity.com", "fidelx"),
        # ("www.morningstar.com", "mrngst"),
        #
        # # Developer, Cloud, & Workspace
        # ("www.github.com", "github"),
        # ("www.gitlab.com", "gitlab"),
        # ("www.stackoverflow.com", "stkovr"),
        # ("www.aws.amazon.com", "awscom"),
        # ("www.cloudflare.com", "cldflr"),
        # ("www.digitalocean.com", "dgtloc"),
        # ("www.npmjs.com", "npmjsp"),
        # ("www.docker.com", "dockrx"),
        # ("www.slack.com", "slackx"),
        # ("www.zoom.us", "zoomus"),
        # ("www.notion.so", "notion"),
        # ("www.figma.com", "figmax"),
        # ("www.canva.com", "canvax"),
        # ("www.dropbox.com", "drpbxm"),
        #
        # # Reference, Science & Medical
        ("www.wikipedia.org", "wikipd"),
        # ("www.britannica.com", "britan"),
        # ("www.nasa.gov", "nasagv"),
        # ("www.nih.gov", "nihgov"),
        # ("www.cdc.gov", "cdcgov"),
        # ("www.nature.com", "nature"),
        # ("www.sciencedirect.com", "scidrt"),
        # ("www.space.com", "spacex"),
        # ("www.wolframalpha.com", "wolpax"),
        #
        # # Entertainment, Gaming & Media
        # ("www.twitch.tv", "twitch"),
        # ("www.steampowered.com", "steamp"),
        # ("www.epicgames.com", "epicgm"),
        # ("www.roblox.com", "roblox"),
        # ("www.ign.com", "igncom"),
        # ("www.gamespot.com", "gmspot"),
        # ("www.patreon.com", "patron"),
        # ("www.bandcamp.com", "bandcp"),
        # ("www.deviantart.com", "devart"),
        # ("www.giphy.com", "giphyx"),
        #
        # # Travel & Logistics
        # ("www.expedia.com", "expedi"),
        # ("www.skyscanner.net", "skyscn"),
        # ("www.uber.com", "uberxx"),
        # ("www.lyft.com", "lyftxx"),
        # ("www.fedex.com", "fedexx"),
        # ("www.ups.com", "upsxxx"),
        # ("www.usps.com", "uspsxx"),
        #
        # # Sports & Hobbies
        # ("www.espn.com", "espnxx"),
        # ("www.nba.com", "nbacom"),
        # ("www.nfl.com", "nflcom"),
        # ("www.strava.com", "strava"),
        # ("www.chess.com", "chessx"),
        # ("www.boardgamegeek.com", "bdgmgk"),
        #
        # # Education & Careers
        # ("www.duolingo.com", "duolng"),
        # ("www.udemy.com", "udemyx"),
        # ("www.glassdoor.com", "glsdrx"),
        # ("www.indeed.com", "indeed"),
        # ("www.monster.com", "mnster"),
        #
        # # Miscellaneous / High Traffic Utilities
        # ("www.speedtest.net", "spdts"),
        # ("www.imgur.com", "imgurx"),
        # ("www.vimeo.com", "vimeox"),
        # ("www.dailymotion.com", "dlymtn"),
        # ("www.weibo.com", "weibox"),
        # ("www.google.com", "google"),
        # ("www.baidu.com", "baidux"),
        # ("www.yandex.ru", "yandex"),
        # ("www.duckduckgo.com", "duckgo"),
        # ("www.yahoo.com", "yahoos"),
        #
        # # Social Media & Communication
        # ("www.facebook.com", "facebk"),
        # ("www.instagram.com", "instag"),
        # ("www.tiktok.com", "tiktok"),
        # ("www.reddit.com", "reddit"),
        # ("www.linkedin.com", "linkdn"),
        # ("www.pinterest.com", "pintr"),
        # ("www.tumblr.com", "tumblx"),
        # ("www.discord.com", "dscord"),
        # ("www.whatsapp.com", "whatsp"),
        # ("www.telegram.org", "telgrm"),
        #
        # # E-Commerce & Retail
        # ("www.amazon.com", "amaznx"),
        # ("www.ebay.com", "ebayxx"),
        # ("www.aliexpress.com", "aliexp"),
        # ("www.etsy.com", "etsyxx")
        # ("www.shopify.com", "shopif"),
        ("www.ikea.com", "ikeaxx")
    ]
    fails = []
    for (site, nsid) in sites:
        status_msg = ""
        Topology.nuke_all()

        def log(m):
            nonlocal status_msg
            status_msg = m
            print(m)
        try:
            # capture the site. (if not already present)
            log(f"capturing {site}")
            capture_site(site, overwrite=False)
            site_res_dir = os.path.join(result_dir, site)
            if os.path.isdir(site_res_dir):
                raise Exception(f"error: {site_res_dir} exists. skipping {site}...")

            log("bringing topology up")
            # first bring the topo up
            topo = Topology(nsid)
            topo.up()

            log("writing global impairements")
            # write our impairements to a file
            os.makedirs(site_res_dir, exist_ok=True)
            with open(os.path.join(site_res_dir, "impairement.txt"), "w") as f:
                json.dump(impairements, f, indent=4)

            # for each impairement...
            for i, imp in enumerate(impairements):
                # created up front so a failure anywhere below still has
                # somewhere to record what happened for this run
                run_dir = os.path.join(site_res_dir, f"run{i}")
                os.makedirs(run_dir, exist_ok=True)
                try:
                    log(f"beginning run{i} (of {site})")
                    first = i == 0
                    topo.apply_impairements(imp["bw"], imp["rtt"], imp["bdp"], first=first, loss=imp["loss"])
                    # let tc/netem settle before measuring, so the first
                    # requests aren't caught mid-reconfiguration
                    time.sleep(5)

                    log("writing local impairements")
                    # ... write individual impairement to a file
                    with open(os.path.join(run_dir, "impairement.txt"), "w") as f:
                        json.dump(imp, f, indent=4)

                    # get certs and DNS configured
                    hostnames = get_hostnames(site)
                    cert_dir = create_certs(hostnames)
                    start_dnsmasq(topo, hostnames, quiche_addr)

                    log("starting quiche")
                    # start quiche
                    quiche.start(topo, site, quiche_addr, 443, cert_dir)
                    # let the server fully come up before measuring
                    time.sleep(5)

                    try:
                        # run browsertime
                        log("running browsertime...")
                        btpath = os.path.join(run_dir, "browsertime")
                        btstats = browsertime.run(topo, site, btpath)
                    except Exception as e:
                        print(f"Error running browsertime:\n{e}")
                        with open(os.path.join(run_dir, "browsertime_FAILED.txt"), "w") as f:
                            f.write(str(e))
                        fails.append(f"{site} run{i} (browsertime)")

                    try:
                        # run lighthouse
                        log("running lighthouse...")
                        lhpath = os.path.join(run_dir, "lighthouse")
                        lhstats = lighthouse.run(topo, site, lhpath)
                    except Exception as e:
                        print(f"Error running lighthouse:\n{e}")
                        with open(os.path.join(run_dir, "lighthouse_FAILED.txt"), "w") as f:
                            f.write(str(e))
                        fails.append(f"{site} run{i} (lighthouse)")

                    # stop server and copy files
                    quiche_path = os.path.join(run_dir, "quiche")
                    quiche.copy_files(topo, quiche_path)
                    quiche.stop(topo)

                    time.sleep(10)
                except Exception as e:
                    # catch the error here so only this one run is lost
                    print(f"Run {i} setup failed for {site}: {e}")
                    with open(os.path.join(run_dir, "run_SETUP_FAILED.txt"), "w") as f:
                        f.write(str(e))
                    fails.append(f"{site} run{i} (setup)")
                    try:
                        quiche.stop(topo)
                    except Exception:
                        pass
                    continue

            # remove topology namespaces
            topo.teardown()
        except Exception as e:
            print(f"ERROR for {site} '{status_msg}'")
            print(e)
            fails.append(site)
            Topology.nuke_all()
    print("Run complete. Errors with the following:")
    for fail in fails:
        print(f" - {fail}")
