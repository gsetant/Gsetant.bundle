# -*- coding: utf-8 -*-

import base64
import json
from lxml import etree
from datetime import datetime

PREFIX = '/video/Gsetant'
NAME = 'Gsetant'
VERSION = 'Beta:0.0.1'
PMS_URL = 'http://127.0.0.1:32400/'

timeout = 3600


def Start():
    HTTP.CacheTime = 0


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
            'video_title': Video_title,
            'part_file': Part_file,
            'video_type': Video_type,
            'video_librarySectionID': Video_librarySectionID,
            'video_librarySectionTitle': Video_librarySectionTitle
        }

        result = None

        try:
            result = HTTP.Request('%s:%s/scan' % (Prefs['Gsetant_api_host'], Prefs['Gsetant_api_port']),
                                  data=json.dumps(values),
                                  timeout=timeout).content
        except Exception as ex:
            Log(ex)

        if result is not None:
            json_data_list = json.loads(result)
            if json_data_list['state']:
                for json_data in json_data_list['meta_data']:
                    id = json.dumps(json_data)
                    name = json_data.get('title')
                    score = 100
                    year = json_data.get('year')
                    thumb = ''
                    new_result = dict(id=id, name=name, year=year, score=score, lang=lang, thumb=thumb)
                    results.Append(MetadataSearchResult(**new_result))

    def update(self, metadata, media, lang):
        json_data_list = json.loads(metadata.id)
        metadata.title = json_data_list.get('title')
        metadata.original_title = json_data_list.get('original_title')
        metadata.summary = json_data_list.get('summary')
        metadata.studio = json_data_list.get('studio')
        for collection in json_data_list.get('collections').split(','):
            metadata.collections.add(collection)
        metadata.originally_available_at = datetime.strptime(
            json_data_list.get('originally_available_at').replace('/', '-'), r'%Y-%m-%d')
        metadata.year = int(json_data_list.get('year').replace('/', '-').split('-')[0])
        metadata.directors.clear()
        metadata.directors.new().name = json_data_list.get('directors')
        genres_list = json_data_list.get('category').split(',')
        for genres_name in genres_list:
            metadata.genres.add(genres_name)
        poster = base64.b64decode(json_data_list.get('poster'))
        metadata.posters[json_data_list.get('poster')] = Proxy.Media(poster)
        art = base64.b64decode(json_data_list.get('thumbnail'))
        metadata.art[json_data_list.get('thumbnail')] = Proxy.Media(art)
        metadata.content_rating = 'R18'

        metadata.roles.clear()
        actors_list = json_data_list.get('actor')
        if actors_list != '':
            for key in actors_list:
                role = metadata.roles.new()
                role.name = key
                actor_base64 = actors_list.get(key)
                actor_img = base64.b64decode(actor_base64)
                role.photo = Proxy.Media(actor_img)


class GsetantForTVShowAgent(Agent.TV_Shows):
    name = NAME + ' TV_Show ' + VERSION
    pass


class ToolsClass():
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
