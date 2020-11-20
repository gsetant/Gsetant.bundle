# -*- coding: utf-8 -*-
import os
import base64
import json
from io import BytesIO
from lxml import etree
from datetime import datetime
import random
import string
import Framework
import errno
import shutil
import stat
import tempfile
import sys
from io import open as iopen
if sys.platform == 'win32':
    import ctypes
    kdll = ctypes.windll.LoadLibrary("kernel32.dll")


load_file = Core.storage.load
logi = Log.Info
loge = Log.Error
logw = Log.Warn
logd = Log.Debug


PREFIX = '/video/Gsetant'
NAME = 'Gsetant'
VERSION = 'Beta:0.0.1'
PMS_URL = 'http://127.0.0.1:32400/'


try:
    PLUGIN_CACHE_PATH = os.path.join(sys.argv[len(sys.argv)-1]+'/Cache/')


except Exception as ex:
    loge(ex)

timeout = 3600


def Start():
    HTTP.CacheTime = 0
    try:
        # 创建缓存目录
        if not os.path.exists(PLUGIN_CACHE_PATH):
            os.makedirs(PLUGIN_CACHE_PATH)
    except Exception as ex:
        loge(ex)
    return


class GsetantForMoviesAgent(Agent.Movies):

    name = NAME + ' Movie ' + VERSION
    languages = [
        Locale.Language.English,
        Locale.Language.Chinese
    ]
    primary_provider = True
    accepts_from = [
        'com.plexapp.agents.localmedia'
    ]
    contributes_to = [
        'com.plexapp.agents.themoviedb',
        'com.plexapp.agents.imdb'
    ]

    def search(self, results, media, lang, manual):
        tc = ToolsClass()
        library_url = 'http://127.0.0.1:32400/library/metadata/%s' % media.id
        base_result = HTTP.Request(library_url, timeout=timeout).content
        xml = etree.XML(base_result)
        Video_ratingKey = xml.xpath('//Video/@ratingKey')[0]
        Video_title = xml.xpath('//Video/@title')[0]
        Part_file = xml.xpath('//Part/@file')[0]
        Video_type = xml.xpath('//Video/@type')[0]
        Video_librarySectionTitle = xml.xpath(
            '//Video/@librarySectionTitle')[0]
        Video_librarySectionID = xml.xpath('//Video/@librarySectionID')[0]

        HTTP.ClearCache()
        HTTP.CacheTime = CACHE_1MONTH
        values = {
            'token': Prefs['Gsetant_token'],
            'autoFlag': False,
            'video_ratingKey': Video_ratingKey,
            'video_title': media.name,
            'part_file': Part_file,
            'video_type': Video_type,
            'video_librarySectionID': Video_librarySectionID,
            'video_librarySectionTitle': Video_librarySectionTitle
        }

        result = None
        try:
            result = HTTP.Request(
                '%s:%s/scan' % (tc.convertHttp(Prefs['Gsetant_api_host']), Prefs['Gsetant_api_port']), data=json.dumps(values), timeout=timeout).content
        except Exception as ex:
            loge(ex)

        if result is not None:
            json_data_list = json.loads(result)
            if json_data_list['state']:
                data_list = json_data_list['meta_data']
                data_list.reverse()
                for json_data in data_list:
                    id = '%s|%s'%(''.join(random.sample(
                        string.ascii_letters + string.digits, 60)),json.dumps(json_data))
                    id = base64.b64encode(id).replace('/', '_')
                    name = json_data.get('title')
                    score = 100
                    year = json_data.get('year')
                    thumb = tc.convertHttp('%s:%s%s' % (
                    Prefs['Gsetant_api_host'], Prefs['Gsetant_api_port'], json_data['thumbnail']))
                    new_result = dict(id=id, name=name, year=year,
                                      score=score, lang=lang, thumb=thumb)

                    results.Append(MetadataSearchResult(**new_result))


    def update(self, metadata, media, lang):        
        tc = ToolsClass()
        data = base64.b64decode(metadata.id.replace("_",'/'))
        logi(data)
        json_data_list = data.split('|')[1]
        logi(json_data_list)
        try:
            json_data_list = json.loads(json_data_list)
            metadata.title = json_data_list['title']
            metadata.original_title = json_data_list['original_title']
            metadata.summary = json_data_list['summary']
            metadata.studio = json_data_list['studio']
            for collection in json_data_list['collections'].split(','):
                metadata.collections.add(collection)
            metadata.originally_available_at = datetime.strptime(
                json_data_list['originally_available_at'].replace('/', '-'), r'%Y-%m-%d')
            metadata.year = int(json_data_list[
                'year'].replace('/', '-').split('-')[0])
            metadata.directors.clear()
            metadata.directors.new().name = json_data_list['directors']
            genres_list = json_data_list['category'].split(',')
            for genres_name in genres_list:
                metadata.genres.add(genres_name)

            # poster
            poster_key = ''.join(random.sample(
                        string.ascii_letters + string.digits, 60))
            poster_url = tc.convertHttp('%s:%s%s' % (
                Prefs['Gsetant_api_host'], Prefs['Gsetant_api_port'], json_data_list['poster']))
            logi('海报缓存:%s' % poster_url)
            poster = HTTP.Request(poster_url)
            metadata.posters[poster_url] = Proxy.Media(poster,sort_order=0)

            # # art
            art_key = ''.join(random.sample(
                        string.ascii_letters + string.digits, 60))
            art_url = tc.convertHttp('%s:%s%s' % (
                Prefs['Gsetant_api_host'], Prefs['Gsetant_api_port'], json_data_list['thumbnail']))
            logi('背景缓存:%s' % art_url)
            art = HTTP.Request(art_url)
            metadata.art[art_url] = Proxy.Media(art,sort_order=0)
            

            # # roles
            metadata.roles.clear()
            actors_list = json_data_list['actor']
            if actors_list != '':
                for key in actors_list:
                    role = metadata.roles.new()
                    role.name = key
                    rule_url = tc.convertHttp('%s:%s%s' % (
                        Prefs['Gsetant_api_host'], Prefs['Gsetant_api_port'], actors_list.get(key)))
                    logi('演员 %s 缓存:%s' % (key,rule_url))
                    photo = HTTP.Request(rule_url)
                    role.photo = rule_url

            metadata.content_rating = 'R18'

        except Exception as ex:
            loge(ex)


class GsetantForTVShowAgent(Agent.TV_Shows):
    name = NAME + ' TV_Show ' + VERSION
    pass


class ToolsClass():

    def loadimage(self, base64_str):
        with open(base64_str, "r") as f:
            image = f.read()
            image_base64 = str(base64.b64encode(image), encoding='utf-8')
            return image_base64

    def convertHttp(self, url):
        if url.find('http://') > -1:
            return url
        if url.find('https://') > -1:
            url = url.replace('https://', '')
            url = 'http"//' + url
            return url
        if url.find('http://') < 0:
            url = 'http://' + url
            return url
