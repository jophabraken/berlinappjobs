# -*- coding: utf-8 -*-
"""Rebuild the whole site from _build/data. Usage: python3 _build/build_all.py
Order matters: guides first (needs /companies/ from the previous build for links), then company/city pages,
then job pages (writes jobpages_map.json), company/city pages again (now linking to job pages), then the homepage."""
import os, runpy, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
for step in ['build_seo.py', 'build_programmatic.py', 'build_jobpages.py', 'build_programmatic.py', 'build_home.py']:
    t = time.time(); print(f'== {step}', flush=True)
    runpy.run_path(os.path.join(HERE, step), run_name='__main__')
    print(f'   done in {time.time() - t:.1f}s', flush=True)
