import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import xmltodict
import json


API_KEY = "77576c4366676b77313033484a544654"

where = str(input("어디로 검색하시겠습니까? : "))

#1. 광화문·덕수궁
url = f'http://openapi.seoul.go.kr:8088/{API_KEY}/xml/citydata/1/5/{where}'
response = requests.get(url)

if response.status_code == 200:
    # XML 데이터를 딕셔너리로 변환
    xml_data = xmltodict.parse(response.text)
            
    # JSON으로 변환
    json_data = json.dumps(xml_data, indent=4, ensure_ascii=False)
    parsed_data = json.loads(json_data)  # JSON String -> Dictionary

    # 안전하게 키 접근
    city_data = parsed_data.get("SeoulRtd.citydata", {}).get("CITYDATA", {})
    
    print(city_data)
    
else :
    print("Error Code:", response.status_code)

