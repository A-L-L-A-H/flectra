#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Batch Two-Pass Importer CLI for all 54 RGBL datasets from bjo163/moonwitness-corpus.

Usage inside flectra-app container:
    python /opt/flectra/addons/moonwitness_sidra/tools/import_all_rgbl.py \
        --corpus-dir /tmp/moonwitness-corpus --db dev --batch-size 1000
"""
import argparse
import os
import sys

TRADITION_HINTS = {
    'quran': 'islam',
    'hadith': 'islam',
    'islamic': 'islam',
    'asmaul': 'islam',
    'bible': 'christianity',
    'sblgnt': 'christianity',
    'early-christian': 'christianity',
    'web-classic': 'christianity',
    'oshb': 'judaism',
    'hebrew': 'judaism',
    'mishnah': 'judaism',
    'dhammapada': 'buddhism',
    'suttacentral': 'buddhism',
    'bhagavad': 'hinduism',
    'upanishads': 'hinduism',
    'yoga': 'hinduism',
    'sanskrit': 'hinduism',
    'tao': 'taoism',
    'zhuangzi': 'taoism',
    'analects': 'confucianism',
    'shinto': 'shinto',
    'sikhism': 'sikhism',
    'jainism': 'jainism',
    'gathas': 'zoroastrianism',
    'bahai': 'bahai',
    'egypt': 'ancient-egyptian',
}


def guess_tradition(dataset_name):
    lower = dataset_name.lower()
    for key, code in TRADITION_HINTS.items():
        if key in lower:
            return code
    return None


def main():
    parser = argparse.ArgumentParser(description='Import all RGBL datasets into MoonWitness Sidra')
    parser.add_argument('--corpus-dir', required=True, help='Path to cloned bjo163/moonwitness-corpus root')
    parser.add_argument('--db', default='dev', help='Flectra PostgreSQL database name')
    parser.add_argument('--conf', default='/etc/flectra/flectra.conf', help='Path to flectra.conf')
    parser.add_argument('--batch-size', type=int, default=1000)
    parser.add_argument('--only', help='Comma-separated dataset folder names to restrict import')
    args = parser.parse_args()

    from flectra.tools import config
    config.parse_config(['-c', args.conf])
    from flectra.modules.registry import Registry
    from flectra.api import Environment

    datasets_root = os.path.join(args.corpus_dir, 'datasets')
    if not os.path.isdir(datasets_root):
        print(f"ERROR: datasets directory not found at {datasets_root}", file=sys.stderr)
        sys.exit(1)

    allowed = set(args.only.split(',')) if args.only else None
    candidates = sorted(
        d for d in os.listdir(datasets_root)
        if os.path.isdir(os.path.join(datasets_root, d))
        and os.path.exists(os.path.join(datasets_root, d, 'manifest.json'))
        and (allowed is None or d in allowed)
    )

    reg = Registry.new(args.db)
    with reg.cursor() as cr:
        env = Environment(cr, 1, {})
        importer = env['moonwitness.sidra.importer.service']
        validator = env['moonwitness.sidra.validator.service']

        grand_total = 0
        for ds in candidates:
            ds_dir = os.path.join(datasets_root, ds)
            trad = guess_tradition(ds)
            try:
                count = importer.import_dataset_from_dir(ds_dir, tradition_code=trad, batch_size=args.batch_size)
                cr.commit()
                grand_total += count
                print(f"[OK] {ds} ({trad or 'auto'}): {count} records")
            except Exception as exc:
                cr.rollback()
                print(f"[ERR] {ds}: {exc}", file=sys.stderr)

        findings = validator.validate_all()
        print(f"\nDONE. Grand total processed: {grand_total} | P1-006 Findings: {len(findings)}")


if __name__ == '__main__':
    main()
