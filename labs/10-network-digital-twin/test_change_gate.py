#!/usr/bin/env python3
"""Synthetic pre/post topology change gate; no production network access."""
import json
from collections import defaultdict

def paths(links, source, dest, disabled=()):
    adj = defaultdict(set)
    for a, b in links:
        if a not in disabled and b not in disabled:
            adj[a].add(b); adj[b].add(a)
    found = []
    def walk(node, seen):
        if node == dest:
            found.append(seen); return
        for nxt in sorted(adj[node] - set(seen)):
            walk(nxt, seen + [nxt])
    if source not in disabled and dest not in disabled:
        walk(source, [source])
    return found

def evaluate(links, denied):
    p = paths(links, 'client', 'app')
    guest = paths(links, 'guest', 'admin')
    return {'client_app_paths': len(p), 'guest_admin_topology_paths': len(guest),
            'guest_admin_effective_paths': 0 if ('guest', 'admin') in denied else len(guest)}

def main():
    base = [('client','leaf1'),('guest','leaf1'),('leaf1','spine1'),('leaf1','spine2'),
            ('spine1','leaf2'),('spine2','leaf2'),('leaf2','app'),('leaf2','admin')]
    denied = {('guest','admin')}
    cases = {
        'baseline': (base, denied, True),
        'spine1_link_removed': ([e for e in base if e != ('leaf1','spine1')], denied, False),
        'segmentation_removed': (base, set(), False),
        'restored': (base, denied, True),
    }
    results = {}
    for name,(links, policy, expected) in cases.items():
        observed = evaluate(links, policy)
        accepted = observed['client_app_paths'] >= 2 and observed['guest_admin_effective_paths'] == 0
        results[name] = {'observed': observed, 'expected_accept': expected, 'actual_accept': accepted,
                         'passed': accepted == expected}
    status = 'pass' if all(x['passed'] for x in results.values()) else 'fail'
    print(json.dumps({'status': status, 'scope': 'synthetic undirected graph only; no BGP/ACL/device verification',
                      'results': results}, ensure_ascii=False, indent=2))
    if status != 'pass': raise SystemExit(1)

if __name__ == '__main__': main()
