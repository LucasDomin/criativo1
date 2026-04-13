#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paletas e dados de países — Studio3"""

COUNTRIES = {
    'BR': {'name':'Brasil','lang':'pt-BR','bg':'#002776','ac':'#FFDF00','bg2':'#001855','flags':['#009C3B','#FFDF00','#002776'],'cta':'SIMULAR AGORA'},
    'AR': {'name':'Argentina','lang':'es-AR','bg':'#141E30','ac':'#74ACDF','bg2':'#0A1220','flags':['#74ACDF','#FFFFFF','#F6B40E'],'cta':'SIMULAR AHORA'},
    'MX': {'name':'México','lang':'es-MX','bg':'#006847','ac':'#FFFFFF','bg2':'#004830','flags':['#006847','#FFFFFF','#CE1126'],'cta':'SIMULAR AHORA'},
    'US': {'name':'United States','lang':'en-US','bg':'#F0F4FF','ac':'#3C3B6E','bg2':'#E0E6FF','flags':['#B22234','#FFFFFF','#3C3B6E'],'cta':'SIMULATE NOW'},
    'JP': {'name':'Japan','lang':'ja-JP','bg':'#0A0A0A','ac':'#BC002D','bg2':'#111111','flags':['#FFFFFF','#BC002D'],'cta':'今すぐシミュレーション'},
    'TR': {'name':'Turkey','lang':'tr-TR','bg':'#0C0000','ac':'#E8001C','bg2':'#180000','flags':['#E8001C','#FFFFFF'],'cta':'HEMEN SİMÜLE ET'},
    'PH': {'name':'Philippines','lang':'en-PH','bg':'#0038A8','ac':'#FCD116','bg2':'#002580','flags':['#0038A8','#CE1126','#FCD116'],'cta':'SIMULATE NOW'},
    'BE': {'name':'Belgium','lang':'fr-BE','bg':'#111111','ac':'#FAE042','bg2':'#1A1A1A','flags':['#000000','#FAE042','#EF3340'],'cta':'SIMULER MAINTENANT'},
    'CO': {'name':'Colombia','lang':'es-CO','bg':'#0A1628','ac':'#FCD116','bg2':'#060D18','flags':['#FCD116','#003087','#CE1126'],'cta':'SIMULAR AHORA'},
    'NL': {'name':'Netherlands','lang':'nl-NL','bg':'#F5F5F5','ac':'#AE1C28','bg2':'#EBEBEB','flags':['#AE1C28','#FFFFFF','#21468B'],'cta':'NU SIMULEREN'},
    'FR': {'name':'France','lang':'fr-FR','bg':'#FAFAFA','ac':'#002395','bg2':'#F0F0F5','flags':['#002395','#FFFFFF','#ED2939'],'cta':'SIMULER MAINTENANT'},
    'UK': {'name':'United Kingdom','lang':'en-GB','bg':'#FAFAFA','ac':'#012169','bg2':'#F0F0F5','flags':['#012169','#FFFFFF','#C8102E'],'cta':'SIMULATE NOW'},
    'KR': {'name':'South Korea','lang':'ko-KR','bg':'#F0F4FF','ac':'#003478','bg2':'#E0E8FF','flags':['#003478','#FFFFFF','#CD2E3A'],'cta':'지금 시뮬레이션'},
    'DE': {'name':'Germany','lang':'de-DE','bg':'#F7F9F4','ac':'#1A7A4A','bg2':'#EEF3EA','flags':['#000000','#DD0000','#FFCE00'],'cta':'JETZT SIMULIEREN'},
    'CZ': {'name':'Czech Republic','lang':'cs-CZ','bg':'#F7F7F7','ac':'#D7141A','bg2':'#EEEEEE','flags':['#D7141A','#FFFFFF','#11457E'],'cta':'SIMULOVAT NYNÍ'},
    'AU': {'name':'Australia','lang':'en-AU','bg':'#F0F4FF','ac':'#00008B','bg2':'#E0E8FF','flags':['#012169','#FFFFFF','#CC0000'],'cta':'SIMULATE NOW'},
    'PT': {'name':'Portugal','lang':'pt-PT','bg':'#003E25','ac':'#FF0000','bg2':'#002818','flags':['#006600','#FF0000','#FFD700'],'cta':'SIMULAR AGORA'},
    'IT': {'name':'Italy','lang':'it-IT','bg':'#F8F8F8','ac':'#009246','bg2':'#EEEEEE','flags':['#009246','#FFFFFF','#CE2B37'],'cta':'SIMULA ORA'},
    'ES': {'name':'Spain','lang':'es-ES','bg':'#AA151B','ac':'#F1BF00','bg2':'#880F14','flags':['#AA151B','#F1BF00'],'cta':'SIMULAR AHORA'},
    'CA': {'name':'Canada','lang':'en-CA','bg':'#F8F8F8','ac':'#FF0000','bg2':'#EEEEEE','flags':['#FF0000','#FFFFFF','#FF0000'],'cta':'SIMULATE NOW'},
    'PE': {'name':'Peru','lang':'es-PE','bg':'#D91023','ac':'#FFFFFF','bg2':'#A50D1A','flags':['#D91023','#FFFFFF','#D91023'],'cta':'SIMULAR AHORA'},
    'GR': {'name':'Greece','lang':'el-GR','bg':'#0D5EAF','ac':'#FFFFFF','bg2':'#0A4A8A','flags':['#0D5EAF','#FFFFFF'],'cta':'ΠΡΟΣΟΜΟΊΩΣΗ ΤΏΡΑ'},
    'TH': {'name':'Thailand','lang':'th-TH','bg':'#F7F7F7','ac':'#A51931','bg2':'#EEEEEE','flags':['#A51931','#FFFFFF','#2D2A4A'],'cta':'จำลองตอนนี้'},
    'ID': {'name':'Indonesia','lang':'id-ID','bg':'#CE1126','ac':'#FFFFFF','bg2':'#A50D1E','flags':['#CE1126','#FFFFFF'],'cta':'SIMULASIKAN SEKARANG'},
    'PL': {'name':'Poland','lang':'pl-PL','bg':'#FAFAFA','ac':'#DC143C','bg2':'#F0F0F0','flags':['#FFFFFF','#DC143C'],'cta':'SYMULUJ TERAZ'},
}

def get_palette(code):
    from engine.core import lum, ctr, atc
    d = COUNTRIES.get(code.upper(), COUNTRIES['US'])
    bg=d['bg']; ac=d['ac']
    if ctr(ac,bg)<4.5:
        ac='#FFFFFF' if lum(bg)<0.30 else '#0A0204'
    return {'bg':bg,'a1':ac,'bg2':d.get('bg2',bg),'flags':d.get('flags',[ac]),
            'cta':d.get('cta','SIMULATE NOW'),'lang':d.get('lang','en-US'),'name':d.get('name',code)}
