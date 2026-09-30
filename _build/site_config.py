# -*- coding: utf-8 -*-
"""Site settings that aren't job data. Edit here; every page picks them up on the next build."""

CONTACT_EMAIL = 'jophabraken@gmail.com'

# Job-alert newsletter. When set (e.g. 'https://buttondown.com/berlinappjobs'), every page's footer shows a
# "Get new app jobs by email" link. The newsletter can be fed automatically from /feed.xml (RSS-to-email).
NEWSLETTER_URL = ''

# Impressum (§ 5 DDG). When set, /impressum/ is built and linked in the footer. Example:
# IMPRESSUM = dict(name='Vorname Nachname', street='Straße 1', city='10115 Berlin', email='…', phone='')
IMPRESSUM = None

# Visit statistics: Umami Cloud (cookieless), loaded after the page by add_analytics.py. Empty UMAMI_ID switches it off.
# Only pageviews and the apply / sponsored / careers click events are sent (the free plan counts every event).
UMAMI_SCRIPT = 'https://cloud.umami.is/script.js'
UMAMI_ID = 'c1c581a7-a262-4d9e-9bbf-d673ab6e5edb'
UMAMI_DOMAINS = 'berlinappjobs.com,www.berlinappjobs.com'   # Umami ignores other hosts (localhost, previews)
