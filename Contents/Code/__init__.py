# -*- coding: utf-8 -*-

import base64
import json
from lxml import etree


PREFIX = '/video/Gsetant'
NAME = 'Gsetant'
VERSION='Beta:0.0.1'
PMS_URL = 'http://127.0.0.1:32400/'

timeout = 3600


def Start():
    HTTP.CacheTime = 0


class GsetantForMoviesAgent(Agent.Movies):
    name = NAME+' Movie '+VERSION
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
            'name': Prefs['Gsetant_LoginName'],
            'password': Prefs['Gsetant_LoginPassword'],
            'video_ratingKey': Video_ratingKey,
            'video_title': Video_title,
            'part_file': Part_file,
            'video_type': Video_type,
            'video_librarySectionID': Video_librarySectionID,
            'video_librarySectionTitle': Video_librarySectionTitle
        }


        result=None

        try:            
            result = HTTP.Request(tc.convertHttp(
                Prefs['Gsetant_api']), values=values, timeout=timeout)
        except Exception as ex:
            Log(ex)        
        
        if result is not None:
            JsonDataList = json.loads(result)
            for JsonDate in JsonDataList:
                id = base64.b64encode('')
                name=''
                score = 100 
                year = '2015'
                thumb=''
                new_result = dict(id=id, name=name, year=year, score=score, lang=lang, thumb=thumb)
                results.Append(MetadataSearchResult(**new_result))


class GsetantForTVShowAgent(Agent.TV_Shows):
    name = NAME+' TV_Show '+VERSION
    pass


class ToolsClass():
    def convertHttp(self, url):
        if url.find('http://') > -1:
            return url
        if url.find('https://') > -1:
            url = url.replace('https://', '')
            url = 'http"//'+url
            return url
        if url.find('http://') < 0:
            url = 'http://'+url
            return url
