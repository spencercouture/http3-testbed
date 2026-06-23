#!/usr/bin/env python3
import os
import json
import numpy as np
import matplotlib.pyplot as plt
import argparse
from collections import Counter


# creates the heatmap graphic for a given results path/website dir
def get_heatmap(site_path):
    obs = []
    try:
        with open(f"{site_path}/quiche/priorities-log.jsonl") as f:
            # cleans the content-type to standardize/remove encoding args
            for line in f:
                line = json.loads(line)
                ctype = "+".join([c.split(";", 1)[0].strip() for c in line["content_type"].split(",")])
                if ctype == "404":
                    continue
                line["content_type"] = ctype
                obs.append(line)
    except Exception:
        return None

    # count urgency/content_type pairs
    freq = Counter((o["urgency"], o["content_type"]) for o in obs)
    labels = sorted({o["content_type"] for o in obs})
    urg_s = range(1, 8)

    # build heatmap matrix
    heatmap = np.array([[freq.get((u, lab), 0) for u in urg_s] for lab in labels])

    # save to
    plt.imshow(heatmap, cmap="Purples", origin="lower", aspect="auto")
    plt.xticks(np.arange(len(urg_s)), urg_s)
    plt.yticks(np.arange(len(labels)), labels)
    plt.colorbar(label="Frequency")
    plt.tight_layout()

    # save to site/graphics/heatmap.png
    outdir = f"{site_path}/graphics"
    os.makedirs(outdir, exist_ok=True)
    outfile = os.path.join(outdir, "heatmap.png")
    plt.savefig(outfile)
    plt.close()
    return outfile


# find (the first) screenshot in browsertime/screenshots/1
def find_screenshot(site_path):
    bt_dir = os.path.join(site_path, "browsertime", "screenshots", "1")
    if os.path.isdir(bt_dir):
        for f in os.listdir(bt_dir):
            if f.lower().endswith((".jpg", ".png")):
                return os.path.join(bt_dir, f)
    return None


# extract some browsertime fields
def extract_bt_fields(site_dir):
    path = os.path.join(site_dir, "browsertime", "browsertime.json")
    try:
        with open(path) as f:
            js = json.load(f)
        d = js[0] if js else {}
        vis = d.get("visualMetrics", {})[0]
        return {
            "FirstVisualChange": vis.get("FirstVisualChange"),
            "SpeedIndex": vis.get("SpeedIndex"),
            "VisualComplete95": vis.get("VisualComplete95")
        }
    except Exception:
        return None


# build HTML row
def build_row(site, screenshot, heatmap, bt_stats):
    s_img = f"<img src='{screenshot}' width='600'>" if screenshot else "<div style='width:600px;height:400px;border:1px solid #ccc;display:flex;align-items:center;justify-content:center;'>No Screenshot</div>"
    h_img = f"<img src='{heatmap}' width='600'>" if heatmap else "<div style='width:600px;height:400px;border:1px solid #ccc;display:flex;align-items:center;justify-content:center;'>No Heatmap</div>"

    stats_html = ""
    if bt_stats:
        stats_html = "<br>".join([f"{k}: {v}" for k, v in bt_stats.items()])

    return (
        f"<tr>"
        f"<td>{site}<br><pre>{stats_html}</pre></td>"
        f"<td>{s_img}</td>"
        f"<td>{h_img}</td>"
        f"</tr>"
    )


# generates a html "report" that contains all the site stats
# sites_dir is the folder that contains all the sites results (the destination/output folder)
# outfile is the name of the html file to be generated
def generate_html(sites_dir, outfile="testbed-results.html"):
    rows = []

    # find each site in the dir
    for site in sorted(os.listdir(sites_dir)):
        site_path = os.path.join(sites_dir, site)
        if not os.path.isdir(site_path):
            continue

        # find the screenshot
        screenshot = find_screenshot(site_path)

        # find the heatmap
        quiche_dir = os.path.join(site_path, "quiche")
        heatmap = get_heatmap(site_path) if os.path.isdir(quiche_dir) else None

        # find the BT stats
        bt_stats = extract_bt_fields(site_path)

        # build the HTML row
        rows.append(build_row(site, screenshot, heatmap, bt_stats))

    # build and return the table
    table = "<table border=1><tr><th>Site</th><th>Screenshot</th><th>Heatmap</th></tr>" + \
        "".join(rows) + "</table>"
    return f"<html><body><h1>Testbed Results</h1>{table}</body></html>"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("site_dir")
    parser.add_argument("-o", "--output", default="testbed-results.html")
    args = parser.parse_args()

    html = generate_html(args.site_dir, args.output)

    print(html)
    with open(args.output, "w") as f:
        f.write(html)


if __name__ == "__main__":
    main()
