#!/usr/bin/env python

# run with --sweep:
#   given a service, looks through current members for those missing an account on that service,
#   and checks that member's official website's source code for mentions of that service.
#   A CSV of "leads" is produced for manual review.
#
# run with --update:
#   reads the CSV produced by --sweep back in and updates the YAML accordingly.

# other options:
#  --service (required): "twitter", "youtube", or "facebook"
#  --bioguide: limit to only one particular member

# uses a CSV at data/social_media_blacklist.csv to exclude known non-individual account names

import csv, re
import utils
from utils import download, load_data, save_data, parse_date

def main():
  debug = utils.flags().get('debug', False)
  bioguide = utils.flags().get('bioguide', None)
  do_update = utils.flags().get('update', False)

  # default to not caching
  cache = utils.flags().get('cache', False)
  force = not cache

  service = utils.flags().get('service', None)
  if service not in ["twitter", "youtube", "facebook"]:
    print "--service must be one of twitter, youtube, or facebook"
    exit(0)

  regexes = {
    "youtube": "http://(?:www\\.)?youtube.com/(?:user/)?([^\\s\"']+)",
    "facebook": "http://(?:www\\.)?facebook.com/(?:home\\.php#!)?(?:#!)?(?:people/)?/?([^\\s\"']+)",
    "twitter": "http://(?:www\\.)?twitter.com/(?:#!/)?@?([^\\s\"']+)"
  }

  print "Loading blacklist..."
  blacklist = {
    'twitter': [], 'facebook': [], 'services': []
  }
  for rec in csv.DictReader(open("data/social_media_blacklist.csv")):
    blacklist[rec["service"]].append(rec["pattern"])

  # load in members, orient by bioguide ID
  print "Loading current legislators..."
  current = load_data("legislators-current.yaml")
  # print "Loading historical legislators..."
  # historical = load_data("legislators-historical.yaml")

  current_bioguide = { }
  for m in current:
    if m["id"].has_key("bioguide"):
      current_bioguide[m["id"]["bioguide"]] = m

  # historical_bioguide = {}
  # for m in historical:
  #   if m["id"].has_key("bioguide"):
  #     historical_bioguide[m["id"]["bioguide"]] = m

  # reorient currently known social media by ID
  print "Loading social media..."
  media = load_data("legislators-social-media.yaml")
  media_bioguide = { }
  for m in media:
    media_bioguide[m["id"]["bioguide"]] = m

  def sweep():
    to_check = []
    for bioguide in current_bioguide.keys():
      if media_bioguide.get(bioguide, None) is None:
        to_check.append(bioguide)
      elif media_bioguide[bioguide]["social"].get(service, None) is None:
        to_check.append(bioguide)
      else:
        pass
    
    utils.mkdir_p("cache/social_media")
    writer = csv.writer(open("cache/social_media/%s_candidates.csv" % service, 'w'))
    writer.writerow(["bioguide", "official_full", "website", "service", "candidate"])

    for bioguide in to_check:
      url = current_bioguide[bioguide]["terms"][-1].get("url", None)
      if not url:
        if debug:
          print "[%s] No official website, skipping" % bioguide
        continue

      if debug:
        print "[%s] Downloading..." % bioguide
      cache = "congress/%s.html" % bioguide
      body = utils.download(url, cache, force)
      match = re.search(regexes[service], body, re.I)
      if match:
        candidate = match.group(1)
        passed = True
        for blacked in blacklist[service]:
          if re.search(blacked, candidate, re.I):
            passed = False
        
        if not passed:
          if debug:
            print "\tBlacklisted: %s" % candidate
          continue

        writer.writerow([bioguide, current_bioguide[bioguide]['name']['official_full'], url, service, candidate])
        print "\tWrote: %s" % candidate

  def update():
    if bioguide:
      bioguides = [bioguide]
    else:
      bioguides = by_bioguide.keys()

    warnings = []
    count = 0

    for bioguide in bioguides:
      
      count = count + 1

    print "Saving data..."
    save_data(legislators, "legislators-current.yaml")

    print "Saved %d legislators" % count

  if do_update:
    update()
  else:
    sweep()

main()