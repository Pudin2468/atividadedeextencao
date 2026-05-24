#!/usr/bin/env python3
"""
Format records CSV for Excel and group into monthly blocks.

Usage:
  python scripts/format_csv.py input.csv output.csv

Produces a UTF-8 with BOM CSV, comma-separated, with block headers
between months and a blank line between blocks so Excel shows clear sections.
"""
import csv
import sys
from datetime import datetime

def month_label(dt):
    return dt.strftime('%Y-%m')

def main():
    if len(sys.argv) < 3:
        print('Usage: format_csv.py input.csv output.csv')
        return 1
    inp = sys.argv[1]
    out = sys.argv[2]

    rows = []
    with open(inp, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            # expect created_at in ISO format
            try:
                r['_dt'] = datetime.fromisoformat(r.get('created_at'))
            except Exception:
                r['_dt'] = None
            rows.append(r)

    # sort by date
    rows.sort(key=lambda r: (r['_dt'] or datetime.min))

    # group by month
    groups = {}
    for r in rows:
        key = month_label(r['_dt']) if r['_dt'] else 'unknown'
        groups.setdefault(key, []).append(r)

    # write with BOM for Excel and comma separator
    bom = '\ufeff'
    fieldnames = [fn for fn in rows[0].keys() if not fn.startswith('_')] if rows else []
    with open(out, 'w', newline='', encoding='utf-8') as f:
        f.write(bom)
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        # We'll write blocks with a header row indicating the block
        for idx, (key, items) in enumerate(sorted(groups.items())):
            # block header as a comment-like row
            f.write(f'# Block: {key}\n')
            writer.writeheader()
            for r in items:
                row = {k: v for k, v in r.items() if not k.startswith('_')}
                writer.writerow(row)
            # blank line between blocks
            if idx < len(groups)-1:
                f.write('\n')

    print('Wrote', out)
    return 0

if __name__ == '__main__':
    sys.exit(main())
