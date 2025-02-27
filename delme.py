#!/usr/bin/env python3
import os
from clients.browsertime import compute_metrics

path = os.path.join("output/full_run4/www.wikipedia.org/browsertime")
print(compute_metrics(path))
