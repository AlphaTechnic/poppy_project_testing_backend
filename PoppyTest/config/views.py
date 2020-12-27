import requests
import openpyxl
import numpy as np
from json import dumps
from haversine import haversine
from django.shortcuts import HttpResponse
from . import samples


def get_lat_lng(address):
    result = ""

    url = 'https://dapi.kakao.com/v2/local/search/address.json?query=' + address
    rest_api_key = '7d66b3ade18db0422c2f27baada16e45'
    header = {'Authorization': 'KakaoAK ' + rest_api_key}

    r = requests.get(url, headers=header)

    if r.status_code == 200:
        result_address = r.json()["documents"][0]["address"]
        result = float(result_address["x"]), float(result_address["y"])
    else:
        result = "ERROR[" + str(r.status_code) + "]"

    return result


def get_address():
    coordinate_start = 126.751286, 37.419093
    coordinate_end = 127.196322, 37.707367
    #0.008
    xvals = np.arange(coordinate_start[0], coordinate_end[0], step=0.008)
    yvals = np.arange(coordinate_start[1], coordinate_end[1], step=0.008)

    write_wb = openpyxl.Workbook()
    write_ws = write_wb.active

    expert_or_not = 1
    even_flag = 0
    numbering = 0
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

            expert_or_not *= (-1)
            if even_flag == 2:
                numbering = (numbering + 1) % 5
                even_flag = 0
            even_flag += 1
            ## 엑셀에 기록
            write_ws.append([x, y, result_address, expert_or_not, numbering])
    write_wb.save('address.xlsx')

    print("서울시 주소 저장 완료")


def get_distance(coordinate1, coordinate2):
    distance = haversine(coordinate1, coordinate2, unit='km')

    return distance


def get_experts(request):
    order_by = request.GET.get('order_by')
    if order_by == "distance":
        address = request.GET.get('address')
        coordinate1 = get_lat_lng(address)

        # data_only=True로 해줘야 수식이 아닌 값으로 받아온다.
        load_wb = openpyxl.load_workbook("address.xlsx", data_only=True)
        load_ws = load_wb['Sheet']

        expert_list = []
        for row in load_ws.rows:
            x2 = row[0].value
            y2 = row[1].value
            address = row[2].value
            expert_or_not = row[3].value

            coordinate2 = x2, y2  # 펫시터 사는 곳 좌표
            new_querySet = x2, y2, address, get_distance(coordinate1, coordinate2), expert_or_not
            if expert_or_not == 1:
                expert_list.append(new_querySet)
                nearest5_experts = sorted(expert_list, key=lambda x: x[3])[:5]
            else:
                continue
        print(nearest5_experts)
        info = dict()
        petsitters = []
        type = round(nearest5_experts[0][3] * 1000) % 5   # 첫번째 펫시터의 거리로 생성한 random number

        for i, petsitter in enumerate(nearest5_experts):
            print(i)
            petsitter_info = dict()
            # petsitter[4] : 전문가 여부
            petsitter_info["expert_or_not"] = 1

            # petsitter[2] : 주소
            petsitter_info["address"] = petsitter[2]

            # petsitter[3] : 떨어진 거리
            if petsitter[3] < 1:
                petsitter_info["distance"] = str(round(petsitter[3] * 1000)) + 'm'
            elif 1 <= petsitter[3] < 10:
                petsitter_info["distance"] = str(round(petsitter[3], 1)) + 'km'
            else:
                petsitter_info["distance"] = str(round(petsitter[3])) + 'km'

            # petsitter[5] : 5가지 유형 중 어떤 petsitter인가
            type = (type + 1) % 5
            petsitter_info["type"] = type

            # title
            petsitter_info["title"] = samples.expert[type]["title"]
            # 방 사진
            petsitter_info["room_img"] = samples.expert[type]["room_img"]
            # 평점
            petsitter_info["score"] = samples.expert[type]["score"]
            # 가격
            petsitter_info["small_dog_cost"] = samples.expert[type]["small_dog_cost"]
            petsitters.append(petsitter_info)
        info["experts"] = petsitters
        return HttpResponse(dumps(info, ensure_ascii=False), content_type=u"application/json; charset=utf-8")

    # elif order_by == "price":
    #     info = dict()
    #     petsitters = []
    #     for i in range(4, -1, -1):
    #         petsitter_info = dict()
    #         # petsitter[4] : 전문가 여부
    #         petsitter_info["expert_or_not"] = 0
    #         # petsitter[2] : 주소
    #         petsitter_info["address"] = samples.non_expert[i]["address"]
    #         # petsitter[3] : 떨어진 거리
    #
    #
    #         if petsitter[3] < 1:
    #             petsitter_info["distance"] = str(round(petsitter[3] * 1000)) + 'm'
    #         elif 1 <= petsitter[3] < 10:
    #             petsitter_info["distance"] = str(round(petsitter[3], 1)) + 'km'
    #         else:
    #             petsitter_info["distance"] = str(round(petsitter[3])) + 'km'
    #
    #         # petsitter[5] : 5가지 유형 중 어떤 petsitter인가
    #         type = (type + i) % 5
    #         petsitter_info["type"] = type
    #         # 방 사진
    #         petsitter_info["room_img"] = samples.non_expert[type]["room_img"]
    #         # 평점
    #         petsitter_info["score"] = samples.non_expert[type]["score"]
    #         # 가격
    #         petsitter_info["small_dog_cost"] = samples.non_expert[type]["small_dog_cost"]
    #
    #     petsitters.append(petsitter_info)
    #
    #
    #     info["petsitters"] = petsitters
    #     return HttpResponse(dumps(info, ensure_ascii=False), content_type=u"application/json; charset=utf-8")

def get_non_experts(request):
    order_by = request.GET.get('order_by')
    if order_by == "distance":
        address = request.GET.get('address')
        coordinate1 = get_lat_lng(address)

        # data_only=True로 해줘야 수식이 아닌 값으로 받아온다.
        load_wb = openpyxl.load_workbook("address.xlsx", data_only=True)
        load_ws = load_wb['Sheet']

        non_expert_list = []
        for row in load_ws.rows:
            x2 = row[0].value
            y2 = row[1].value
            address = row[2].value
            expert_or_not = row[3].value

            coordinate2 = x2, y2  # 펫시터 사는 곳 좌표
            new_querySet = x2, y2, address, get_distance(coordinate1, coordinate2), expert_or_not
            if expert_or_not == -1:
                non_expert_list.append(new_querySet)
                non_nearest5_experts = sorted(non_expert_list, key=lambda x: x[3])[:5]
            else:
                continue

        info = dict()
        petsitters = []
        type = round(non_nearest5_experts[0][3] * 1000) % 5   # 첫번째 펫시터의 거리로 생성한 random number

        for i, petsitter in enumerate(non_nearest5_experts):
            petsitter_info = dict()
            # petsitter[4] : 전문가 여부
            petsitter_info["expert_or_not"] = 1

            # petsitter[2] : 주소
            petsitter_info["address"] = petsitter[2]

            # petsitter[3] : 떨어진 거리
            if petsitter[3] < 1:
                petsitter_info["distance"] = str(round(petsitter[3] * 1000)) + 'm'
            elif 1 <= petsitter[3] < 10:
                petsitter_info["distance"] = str(round(petsitter[3], 1)) + 'km'
            else:
                petsitter_info["distance"] = str(round(petsitter[3])) + 'km'

            # petsitter[5] : 5가지 유형 중 어떤 petsitter인가
            type = (type + 1) % 5
            petsitter_info["type"] = type

            # title
            petsitter_info["title"] = samples.expert[type]["title"]
            # 방 사진
            petsitter_info["room_img"] = samples.expert[type]["room_img"]
            # 평점
            petsitter_info["score"] = samples.expert[type]["score"]
            # 가격
            petsitter_info["small_dog_cost"] = samples.expert[type]["small_dog_cost"]
            petsitters.append(petsitter_info)
        info["non_experts"] = petsitters
        return HttpResponse(dumps(info, ensure_ascii=False), content_type=u"application/json; charset=utf-8")

    # elif order_by == "price":
    #     info = dict()
    #     petsitters = []
    #     for i in range(4, -1, -1):
    #         petsitter_info = dict()
    #         # petsitter[4] : 전문가 여부
    #         petsitter_info["expert_or_not"] = 0
    #         # petsitter[2] : 주소
    #         petsitter_info["address"] = samples.non_expert[i]["address"]
    #         # petsitter[3] : 떨어진 거리
    #
    #
    #         if petsitter[3] < 1:
    #             petsitter_info["distance"] = str(round(petsitter[3] * 1000)) + 'm'
    #         elif 1 <= petsitter[3] < 10:
    #             petsitter_info["distance"] = str(round(petsitter[3], 1)) + 'km'
    #         else:
    #             petsitter_info["distance"] = str(round(petsitter[3])) + 'km'
    #
    #         # petsitter[5] : 5가지 유형 중 어떤 petsitter인가
    #         type = (type + i) % 5
    #         petsitter_info["type"] = type
    #         # 방 사진
    #         petsitter_info["room_img"] = samples.non_expert[type]["room_img"]
    #         # 평점
    #         petsitter_info["score"] = samples.non_expert[type]["score"]
    #         # 가격
    #         petsitter_info["small_dog_cost"] = samples.non_expert[type]["small_dog_cost"]
    #
    #     petsitters.append(petsitter_info)
    #
    #
    #     info["petsitters"] = petsitters
    #     return HttpResponse(dumps(info, ensure_ascii=False), content_type=u"application/json; charset=utf-8")

def get_expert(request, type):
    petsitter_info = dict()

    # petsitter[4] : 전문가 여부
    petsitter_info["expert_or_not"] = 1

    # 방 사진
    petsitter_info["room_img"] = samples.expert[type]["room_img"]
    # 이름
    petsitter_info["name"] = samples.expert[type]["name"]
    # title
    petsitter_info["title"] = samples.expert[type]["title"]
    # content
    petsitter_info["content"] = samples.expert[type]["content"]
    # 댓글
    petsitter_info["comment"] = samples.expert[type]["comment"]
    # 자격증
    petsitter_info["certification"] = samples.expert[type]["certification"]
    # 평점
    petsitter_info["score"] = samples.expert[type]["score"]

    return HttpResponse(dumps(petsitter_info, ensure_ascii=False), content_type=u"application/json; charset=utf-8")

def get_non_expert(request, type):
    petsitter_info = dict()

    # petsitter[4] : 전문가 여부
    petsitter_info["expert_or_not"] = 0

    # 방 사진
    petsitter_info["room_img"] = samples.non_expert[type]["room_img"]
    # 이름
    petsitter_info["name"] = samples.non_expert[type]["name"]
    # title
    petsitter_info["title"] = samples.non_expert[type]["title"]
    # content
    petsitter_info["content"] = samples.non_expert[type]["content"]
    # 댓글
    petsitter_info["comment"] = samples.non_expert[type]["comment"]
    # 평점
    petsitter_info["score"] = samples.non_expert[type]["score"]

    return HttpResponse(dumps(petsitter_info, ensure_ascii=False), content_type=u"application/json; charset=utf-8")