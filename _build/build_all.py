# -*- coding: utf-8 -*-
"""Rebuild the whole site from _build/data. Usage: python3 _build/build_all.py
Order matters: guides first (needs /companies/ from the previous build for links), then company/city pages,
then job pages (writes jobpages_map.json), company/city pages again (now linking to job pages),
guides again (so company links match the final /companies/), company/city pages once more (writes the full
sitemap.xml, which build_seo.py overwrites with a short one), removal of pages no longer in that sitemap,
then the homepage, and last the favicon files (make_icons.py)."""
import os, runpy, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
for step in ['build_seo.py', 'build_programmatic.py', 'build_jobpages.py', 'build_programmatic.py', 'build_seo.py', 'build_programmatic.py', 'cleanup_stale.py', 'build_home.py', 'make_icons.py']:
    t = time.time(); print(f'== {step}', flush=True)
    runpy.run_path(os.path.join(HERE, step), run_name='__main__')
    print(f'   done in {time.time() - t:.1f}s', flush=True)
