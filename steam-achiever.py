# encoding: utf-8
import json
import urllib2
import sys

import pickle
import os
import logging
import optparse
from decimal import *


class Steam:

  STEAM_BASE_URL = 'http://api.steampowered.com'

  def __init__(self, steam_id, steam_key):
    self.id = steam_id
    self.key = steam_key

  def _api(self, api):
    j = None
    url = '%s/%s' % (self.STEAM_BASE_URL, api)
    j = urllib2.urlopen(url)
    return json.load(j)

  def getOwnedGames(self):
    j = self._api('IPlayerService/GetOwnedGames/v0001/?key=%s&steamid=%s&include_appinfo=1' % (self.key, self.id))
    return j['response']['games']

  def getPlayerAchievements(self, appid):
    j = self._api('ISteamUserStats/GetPlayerAchievements/v0001/?appid=%s&key=%s&steamid=%s&l=en-US' % (str(appid), self.key, self.id))
    return j['playerstats']


class SteamAchiever:

  def __init__(self, steam):
    self.steam = steam
    self.games = None
    self.achievements = None
    self.games_cache = 'steam-%s-games-cache' % steam.id
    self.achievements_cache = 'steam-%s-achievements-cache' % steam.id

  def loadGames(self, force = False):
    if os.path.exists(self.games_cache) and not force:
      logging.debug('loading games from cache')
      self.games = pickle.load(open(self.games_cache, 'r'))
    else:
      logging.debug('getting games list')
      self.games = self.steam.getOwnedGames()
      pickle.dump(self.games, open(self.games_cache, 'w'))

  def loadAchievements(self, force = False):
    if os.path.exists(self.achievements_cache) and not force:
      logging.debug('loading achievements from cache')
      self.achievements = pickle.load(open(self.achievements_cache, 'r'))
    else:
      self.loadGames()
      self.achievements = {}
      for g in self.games:
        logging.debug('getting achievements for %s' % g['name'].encode('utf-8'))
        try:
          a = steam.getPlayerAchievements(g['appid'])
          self.achievements[g['appid']] = a['achievements']
        except:
          logging.debug('error getting achievements for %s' % g['name'].encode('utf-8'))
      pickle.dump(self.achievements, open(self.achievements_cache, 'w'))

  def calcAchieved(self, achievements):
    count = 0
    for a in achievements:
      if a['achieved'] == True:
        count += 1
    total = len(achievements)
    return count, total, Decimal((Decimal(count)/Decimal(total))*100).to_integral_value(), total-count

  def summary(self, sortBy = 'percent'):
    self.loadGames()
    self.loadAchievements()

    gamesdict = {}
    for g in self.games:
      gamesdict[g['appid']] = g

    progress = []
    for appid,a in self.achievements.items():
      s = self.calcAchieved(a)
      progress += [[gamesdict[appid]['name'], s[0], s[1], s[2], s[3]]]

    if sortBy == 'percent':
      for p in sorted(progress, key=lambda p: p[3]):
        print '%3s%% (%2s of %2s, +%2s) %s' % (p[3], p[1], p[2], p[4], p[0].encode('utf-8'))
    elif sortBy == 'total':
      for p in sorted(progress, key=lambda p: p[4]):
        print '%3s%% (%2s of %2s, +%2s) %s' % (p[3], p[1], p[2], p[4], p[0].encode('utf-8'))


if __name__ == '__main__':

  parser = optparse.OptionParser()
  parser.add_option('-r', '--refresh', action='store_true', default=False, help='Force refresh of cached games and achievements')
  parser.add_option('-s', '--sortby', dest='sortby', default='percent', help='Set sort order of achievements, "percent" or "total"')
  parser.add_option('-k', '--key', dest='key', help='Steam API key')
  parser.add_option('-i', '--id', dest='id', help='Steam ID')
  (options, args) = parser.parse_args()

  logging.basicConfig(level = logging.DEBUG)

  if not options.key or not options.id:
    parser.print_help()
    parser.error('you must supply a steam key and ID')
  else:
    steam = Steam(options.id, options.key)
    achiever = SteamAchiever(steam)
    achiever.summary(options.sortby)

