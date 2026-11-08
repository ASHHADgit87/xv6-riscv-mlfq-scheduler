#!/usr/bin/env python3
"""Print mean/min/max per scenario, variant and process kind from results/results.csv."""
import csv, collections, os, statistics as st
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = list(csv.DictReader(open(os.path.join(ROOT, 'results', 'results.csv'))))
agg = collections.defaultdict(list)
for r in rows:
  agg[(r['scenario'], r['variant'], r['kind'])].append(r)
for k in sorted(agg):
  v = agg[k]
  w = [int(x['wall_ticks']) for x in v]
  print('%-14s %-15s %-3s n=%-2d wall mean=%7.1f min=%4d max=%4d | cpu_ms=%6.0f nsched=%6.0f final_prio=%s' % (
    k + (len(v), st.mean(w), min(w), max(w), st.mean(int(x['cpu_ms']) for x in v),
         st.mean(int(x['nsched']) for x in v), sorted(set(x['final_prio'] for x in v)))))
