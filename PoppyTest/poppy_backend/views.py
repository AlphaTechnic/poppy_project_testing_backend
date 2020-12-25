import requests
import openpyxl
import numpy as np
from json import dumps
from haversine import haversine
from django.shortcuts import HttpResponse


def get_lat_lng(address):
    result = ""

    url = 'https://dapi.kakao.com/v2/local/search/address.json?query=' + address
    rest_api_key = '7d66b3ade18db0422c2f27baada16e45'
    header = {'Authorization': 'KakaoAK ' + rest_api_key}

    r = requests.get(url, headers=header)

    if r.status_code == 200:
        result_address = r.json()["documents"][0]["address"]
        result = result_address["x"], result_address["y"]
    else:
        result = "ERROR[" + str(r.status_code) + "]"

    return result


def get_address():
    expert_or_not = 1
    coordinate_start = 126.751286, 37.419093
    coordinate_end = 127.196322, 37.707367

    xvals = np.arange(coordinate_start[0], coordinate_end[0], step=0.007)
    yvals = np.arange(coordinate_start[1], coordinate_end[1], step=0.007)

    write_wb = openpyxl.Workbook()
    write_ws = write_wb.active

    for x in xvals:
        for y in yvals:
            result_address = ""

            url = 'https://dapi.kakao.com/v2/local/geo/coord2regioncode.json?x={}&y={}'.format(x, y)
            rest_api_key = '7d66b3ade18db0422c2f27baada16e45'
            header = {'Authorization': 'KakaoAK ' + rest_api_key}

            r = requests.get(url, headers=header)

            if r.status_code == 200:
                result_address = r.json()["documents"][0]["address_name"]
            else:
                result_address = "ERROR[" + str(r.status_code) + "]"

            if result_address[0:2] != '서울':
                continue

            expert_or_not = expert_or_not * (-1)
            ## 엑셀에 기록
            write_ws.append([x, y, result_address, expert_or_not])
    write_wb.save('address.xlsx')

    print("서울시 주소 저장 완료")


def get_distance(coordinate1, coordinate2):
    distance = haversine(coordinate1, coordinate2, unit='km')
    return distance


def get_close_users(request, address):
    coordinate1 = get_lat_lng(address)

    # data_only=True로 해줘야 수식이 아닌 값으로 받아온다.
    load_wb = openpyxl.load_workbook("address.xlsx", data_only=True)
    load_ws = load_wb['Sheet']

    tmp_list = []
    for row in load_ws.rows:
        x2 = row[0].value
        y2 = row[1].value
        address = row[2]
        expert_or_not = row[3]

        coordinate2 = x2, y2  # 펫시터 사는 곳 좌표
        new_querySet = x2, y2, address, get_distance(coordinate1, coordinate2), expert_or_not
        tmp_list.append(new_querySet)
    top5 = sorted(tmp_list, key=lambda x: x[3])[:5]

    info = dict()
    petsitters = []
    for i in top5:
        petsitter_info = dict()
        # i[2] : 주소
        petsitter_info["address"] = i[2].value

        # i[3] : 떨어진 거리
        if i[3] < 1:
            petsitter_info["distance"] = str(round(i[3]*1000)) + ' m'
        elif 1<= i[3] < 10:
            petsitter_info["distance"] = str(round(i[3], 1)) + 'km'
        else:
            petsitter_info["distance"] = str(round(i[3])) + 'km'

        # i[4] : 전문가 여부
        if i[4] == 1:
            petsitter_info["expert_or_not"] = "전문펫시터"
        else:
            petsitter_info["expert_or_not"] = "이웃돌보미"
        petsitters.append(petsitter_info)
    info["petsitters"] = petsitters

    return HttpResponse(dumps(info), content_type='application/json')
