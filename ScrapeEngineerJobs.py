#!/usr/bin/env python
from bs4 import BeautifulSoup   # Parsing HTML
from collections import deque
from datetime import datetime
import csv
import re
import sys
import urllib2
import argparse

HOST = 'http://www.engineerjobs.com'
FIELDS = ('title', 'company', 'city', 'date', 'url')

jobs = []
pageQueue = deque()
pageNumber = 0

parser = argparse.ArgumentParser(description='Download jobs from engineerjobs.com')
parser.add_argument('--state', default='illinois')
parser.add_argument('--city', default='chicago')
parser.add_argument('--title', default='software-engineering')
parser.add_argument('--radius', default='15')
parser.add_argument('--language', default='c-sharp',
    choices = [
        'actionscript',
        'ada',
        'assembly',
        'c',
        'c-sharp',
        'c-plusplus',
        'cobol',
        'coldfusion',
        'delphi',
        'erlang',
        'fortran',
        'java',
        'javascript',
        'lisp',
        'dot-net',
        'objective-c',
        'perl',
        'php',
        'python',
        'ruby',
        'scala',
        'smalltalk',
        'tcl',
        'visual-basic'])
parser.add_argument('--url', required=False, default='', help='Direct URL override')
args = parser.parse_args()

if not args.url:
    args.url = '%s/jobs/%s/%s/%s/%s.php?r=%s' % (HOST, args.title, args.language, args.state, args.city, args.radius)

# Queue first page
pageQueue.append(args.url)

# Process pages in queue
while pageQueue:
    url = pageQueue.popleft()
    html = None
    file = None
    
    # Status
    pageNumber += 1
    print('Page %d (%d jobs): %s' % (pageNumber, len(jobs), url))
    
    # Read HTML from URL
    try:
        file = urllib2.urlopen(url)
        html = file.read()
        file.close()
    except urllib2.URLError as e:
        print('Could not get page <%s>: %s' % (url, e.msg))
        continue

    # Parse HTML page
    dom = BeautifulSoup(html)
    
    # Parse each job listing
    for row in dom.select('tr.featured'):
        job = {'title':None, 'city':None, 'company':None, 'date':None}
        
        # Get URL from the <a onclick='...'> on the row
        # e.g. onclick="window.location=indClick('/jobdetails.php?mo=r&ad=...', '8276')
        # We want the relative URL between the first two single quotes: /jobdetails.php?mo=r&ad=...
        job['url'] = row['onclick']
        m = re.search("\('([^']*)',", job['url'])
        if m:
            job['url'] = HOST + m.group(1)        
        
        job['title'], job['city'], job['company'], job['date'] = [i.string for i in row.find_all('td')]
        jobs.append(job)
    
    # Add next page to queue
    nextUrls = dom.select('div.content-wrap #search-results div.pagination-container ul.pagination li.next > a')
    if nextUrls:
        pageQueue.extend([HOST + link['href'] for link in nextUrls])

# Output CSV file
print('Found %d jobs' % len(jobs))
date = datetime.today().strftime('%Y-%m-%d %I.%M')
with open('engineerjobs.com %s %s %s.csv' % (args.language, args.state, date), 'wb') as csvFile:
    writer = csv.writer(csvFile)
    writer.writerow([field.title() for field in FIELDS])
    rows = [[job[field].encode('utf-8') for field in FIELDS] for job in jobs]
    writer.writerows(rows)
print('Done')