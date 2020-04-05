from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer

import requests
import json

import cv2 as cv
import numpy as np
import os
from sklearn.linear_model import LinearRegression
from statistics import mode, median
from scipy.stats import kurtosis, skew

def find_strength(rating):
    strong_avg_weak = []
    for rate in rating:
        if rate >= 3.75:
            strong_avg_weak.append("strong")
        elif rate < 1.75:
            strong_avg_weak.append("weak")
        else:
            strong_avg_weak.append("avg")
    return strong_avg_weak

def split_by_marks(predict_frac):
    analysis = []
    for score in predict_frac:
        if score > 0.88:
            analysis.append("Good")
        elif score > 0.80 and score < 0.88:
            analysis.append("Can Be Good")
        elif score > 0.35 and score < 0.65:
            analysis.append("Can Improve")
        elif score < 0.35:
            analysis.append("Poor")
        else:
            analysis.append("Avg")
    return analysis

def rate(rating):
    rating[np.where(rating <= 0)] = 0
    rating[np.where((rating > 0) & (rating < 0.25))] = 0.25
    rating[np.where((rating > 0.25) & (rating < 0.5))] = 0.5
    rating[np.where((rating > 0.5) & (rating < 0.75))] = 0.75
    rating[np.where(rating > 0.75)] = 1

    return rating

def scale(scores, threshold):
    rating = np.zeros_like(scores)
    rating[np.where(scores > threshold)] = 1 
    return rating

@api_view(['GET',])
def sectionWiseAPIView(request):
    data = request.GET
    try:
        atten = np.asarray(json.loads(data['attendance_frac']), dtype=np.float32)
        chpt_num = int(data["chpt_num"])
        test_marks = np.asarray(json.loads(data["test_marks"]), dtype=np.float32)

    #   <Ranks..
        temp_marks = test_marks.argsort()
        ranks_this_test = np.empty_like(temp_marks)
        ranks_this_test[temp_marks] = np.arange(len(test_marks))
        ranks_this_test += 1

        marks_o = np.zeros_like(test_marks, dtype=np.float32)
    #   ..Ranks>

        data_send={
            "mean" : float(np.around(np.mean(test_marks))),
            "std" : float(np.around(np.std(test_marks))),
            "skew":float(np.around(skew(test_marks), decimals=3)),
            "kurt":float(np.around(kurtosis(test_marks), decimals=3)),
            "ranks_this_test":(np.around(ranks_this_test).tolist()),
        }
        for i in range(chpt_num):
            ch_data = json.loads(data["ch"+ str(i+1)])
            m = np.asarray(json.loads(ch_data['marks']), dtype=np.float32)
            max_m = int(ch_data['max_marks'])
            m_frac = np.true_divide(m, max_m)
            num = int(ch_data['num_test'])
            try:
                prev_all_m = np.asarray(json.loads(ch_data['prev_all_marks_frac']), dtype=np.float32)
                all_growth = np.asarray(json.loads(ch_data['all_growth_frac']), dtype=np.float32)
                prev_all_m_avg = prev_all_m/num
                all_growth_avg = all_growth/num
                print(atten.shape, prev_all_m.shape, all_growth_avg.shape)
                X = np.concatenate((atten.reshape(-1,1),prev_all_m_avg.reshape(-1,1), all_growth_avg.reshape(-1,1)), axis=1)
                model = LinearRegression()
                model.fit(X, m_frac)
                predict_frac = model.predict(X)
                expect_minus_actual_frac = m_frac - predict_frac

            except KeyError:
                expect_minus_actual_frac = np.zeros(m.shape)
                all_growth = np.zeros(m.shape)

            try:
                prev_m = np.asarray(json.loads(ch_data['prev_marks']), dtype=np.float32)
                max_prev_marks = json.loads(ch_data["max_prev_marks"])
                prev_m_frac = prev_m/max_prev_marks
                growth_frac = m_frac - prev_m_frac

            except KeyError:
                growth_frac = np.zeros(m.shape)

            prev_all_m += prev_m_frac

            ind = np.where(m==0)
            m[ind] = predict_frac[ind] * max_m
            growth_frac[ind] = 0

            all_growth += growth_frac

    #   <Ratings..
            max_growth = float(np.max(all_growth)) if np.max(all_growth) != 0 else 1e-3
            growth_rating = all_growth/max_growth
            growth_rating = rate(growth_rating) * 2
            max_growth_ = float(np.max(growth_frac)) if np.max(growth_frac) != 0 else 1e-3
            growth_rating_now = growth_frac/max_growth_
            growth_rating_now = rate(growth_rating_now) * 1
            growth_rating += growth_rating_now
            marks_rating = m / np.max(m)
            marks_rating = rate(marks_rating) * 1

            above_avg_rating = scale(predict_frac, np.mean(predict_frac)) * 1

            rating = growth_rating + marks_rating + above_avg_rating
            strong_avg_weak = find_strength(rating)
    #   ..Ratings>

    #   <Ranks..
            marks_o += 3*all_growth + m/max_m + expect_minus_actual_frac
    #   ..Ranks>


    #   <SimpleStats..
            mean_prev_all = np.mean(prev_all_m)
            std_prev_all = np.std(prev_all_m)
            mean_now = np.mean(m)
            std_now = np.std(m)
    #   ..SimpleStats>
    #   <Splitting..
            analysis = split_by_marks(predict_frac)
    #   ..Splitting>

            ch_data = {
                "mean_prev_all":float(np.around(mean_prev_all, decimals=3)),
                "mean_now":float(np.around(mean_now, decimals=3)),
                "std_prev_all":float(np.around(std_prev_all, decimals=3)),
                "std_now":float(np.around(std_now, decimals=3)),
                "expect_minus_actual_frac" : json.dumps(np.around(expect_minus_actual_frac, decimals=3).tolist()),
                "prev_all_frac":json.dumps(np.around(prev_all_m, decimals=3).tolist()),
                "all_growth_frac":json.dumps(np.around(all_growth, decimals=3).tolist()),
                "growth_rating" : json.dumps(growth_rating.tolist()),
                "marks_rating" : json.dumps(marks_rating.tolist()),
                "above_avg_rating" : json.dumps(above_avg_rating.tolist()),
                "analysis" : json.dumps(analysis),
                "strong_avg_weak" : json.dumps(strong_avg_weak),
            }
            data_send["ch"+str(i+1)] = json.dumps(ch_data)

    # <Ranks..
        temp_marks = marks_o.argsort()
        ranks_o = np.empty_like(temp_marks)
        ranks_o[temp_marks] = np.arange(len(marks_o))
        ranks_o += 1
    #   ..Ranks>

        data_send["ranks_o"]=json.dumps(ranks_o.tolist())

        return Response(data_send)
    except KeyError:
        return Response("Beware! Not the correct format of data you are sending.")

def test(request):
    ch1 = {
        "num_test":json.dumps(5),
        "prev_all_marks_frac":json.dumps([3.35,4.67,2.9,1.79,4.89]),
        # "all_growth_frac":json.dumps([0.12, 0.3, -0.1, -0.07, 0.35]),
        "all_growth_frac":json.dumps([0,0,0,0,0]),
        "marks":json.dumps([57,79,35,89,75]),
        "max_marks":json.dumps(100),
        "prev_marks":json.dumps([67,32,54,22,87]),
        "max_prev_marks":json.dumps(100),
    }

    data = {
        "attendance_frac":json.dumps([0.4,0.6,0.78,0.96,1]),
        "bottomThreshold":json.dumps([0.3,0.5]),
        "topThreshold": json.dumps([0.88,0.92]),
        "test_marks":json.dumps([57,79,35,89,75]),
        "chpt_num" : json.dumps(1),
        "ch1":json.dumps(ch1),
    }
    r = requests.get(url = "http://127.0.0.1:8000/stats/", params=data)
    print(r)
    return HttpResponse(r)