#!/usr/bin/env python3
import os
import json
import argparse
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter


# find screenshot in BrowserTime dir
def find_screenshot(path):
    bt_dir = os.path.join(path, "BrowserTime", "screenshots")
    if os.path.isdir(bt_dir):
        for f in os.listdir(bt_dir):
            if f.lower().endswith((".jpg", ".png")):
                return os.path.join(bt_dir, f)
    return None

# generate heatmap PNG if priorities-log.jsonl exists


def make_heatmap(quiche_dir, outdir, site):
    path = os.path.join(quiche_dir, "priorities-log.jsonl")
    if not os.path.isfile(path):
        return None

    obs = []
    with open(path) as f:
        for line in f:
            line = json.loads(line)
            ctype = "+".join([c.split(";", 1)[0].strip()
                             for c in line["content_type"].split(",")])
            if ctype == "404":
                continue
            line["content_type"] = ctype
            obs.append(line)

    freq = Counter((o["urgency"], o["content_type"]) for o in obs)
    labels = sorted({o["content_type"] for o in obs})
    urg_s = range(1, 8)
    heatmap = np.array([[freq.get((u, la), 0)
                         for u in urg_s] for la in labels])

    plt.imshow(heatmap, cmap="Purples", origin="lower", aspect="auto")
    plt.xticks(np.arange(len(urg_s)), urg_s)
    plt.yticks(np.arange(len(labels)), labels)
    plt.colorbar(label="Frequency")
    plt.tight_layout()

    os.makedirs(outdir, exist_ok=True)
    outfile = os.path.join(outdir, f"{site}_heatmap.png")
    plt.savefig(outfile)
    plt.close()
    return outfile

# build HTML table row


def build_row(site, screenshot, heatmap):
    s_img = screenshot if screenshot else "placeholder.png"
    h_img = heatmap if heatmap else "placeholder.png"
    return f"<tr><td>{site}</td><td><img src='{s_img}' width='300'></td><td><img src='{h_img}' width='300'></td></tr>"

# generate full HTML


def generate_html(root, outdir):
    rows = []
    for site in sorted(os.listdir(root)):
        site_path = os.path.join(root, site)
        if not os.path.isdir(site_path):
            continue

        screenshot = find_screenshot(site_path)
        quiche_dir = os.path.join(site_path, "quiche")
        heatmap = make_heatmap(quiche_dir, outdir, site) if os.path.isdir(
            quiche_dir) else None
        rows.append(build_row(site, screenshot, heatmap))

    table = "<table border=1><tr><th>Site</th><th>Screenshot</th><th>Heatmap</th></tr>" + \
        "".join(rows) + "</table>"
    return f"<html><body><h1>Batch Report</h1>{table}</body></html>"

# main


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default="batch5")
    parser.add_argument("-o", "--output", default="report.html")
    parser.add_argument("--imgdir", default="generated_imgs")
    args = parser.parse_args()

    html = generate_html(args.root, args.imgdir)
    with open(args.output, "w") as f:
        f.write(html)


if __name__ == "__main__":
    main()
