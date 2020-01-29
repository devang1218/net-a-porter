from flask import Flask,jsonify,request
import json
import pandas as pd
from functools import partial
from flask_cors import CORS
from flask import request
import gdown
import flask
import io
import os

url = 'https://drive.google.com/a/greendeck.co/uc?id=19r_vn0vuvHpE-rJpFHvXHlMvxa8UOeom&export=download'

# Create Flask application
app = Flask(__name__)

CORS(app)

#website_id's other than NAP    
l = ['5da94f4e6d97010001f81d72', '5da94f270ffeca000172b12e', '5d0cc7b68a66a100014acdb0', '5da94ef80ffeca000172b12c', '5da94e940ffeca000172b12a']

@app.route("/",methods = ["GET"])
def get_function():
    return("Hello ,Welcome to the net a porter service...")

@app.route("/netaporter",methods = ["POST"])
def post_function():
    query = request.get_json()


#1. NAP products where discount is greater than n%
    if query["query_type"]=="discounted_products_list":
        if query["filters"][0]["operand1"]=="discount":
            l1=[]
            if query["filters"][0]["operator"]==">":
                for i in range(len(df["price"])):
                    if ((df["price"][i]["regular_price"]["value"]-df["price"][i]["offer_price"]["value"])>query["filters"][0]["operand2"]):
                        l1.append(str(df["_id"][i]))
            if query["filters"][0]["operator"]=="==":
                for i in range(len(df["price"])):
                    if ((df["price"][i]["regular_price"]["value"]-df["price"][i]["offer_price"]["value"])==query["filters"][0]["operand2"]):
                        l1.append(str(df["_id"][i]))
            if query["filters"][0]["operator"]=="<":
                for i in range(len(df["price"])):
                    if ((df["price"][i]["regular_price"]["value"]-df["price"][i]["offer_price"]["value"])<query["filters"][0]["operand2"]):
                        l1.append(str(df["_id"][i]))
            return jsonify({"discounted_products_list":l1})

        if query["filters"][0]["operand1"]=="brand.name":
            l1=[]
            if query["filters"][0]["operator"]=="==":
                for i in range(len(df["brand"])):
                    if (df["brand"][i]["name"]==query["filters"][0]["operand2"]):
                        l1.append(str(df["_id"][i]))
            return jsonify({"discounted_products_list":l1})

#2. Count of NAP products from a particular brand and its average discount        
    if query["query_type"]=="discounted_products_count|avg_discount":
        c=0
        dis_summ=0
        if query["filters"][0]["operand1"]=="discount":
            if query["filters"][0]["operator"]==">":
                for i in range(len(df["price"])):
                    if ((df["price"][i]["regular_price"]["value"]-df["price"][i]["offer_price"]["value"])>query["filters"][0]["operand2"]):
                        dis_summ+=(df["price"][i]["regular_price"]["value"]-df["price"][i]["offer_price"]["value"])
                        c+=1
            if query["filters"][0]["operator"]=="==":
                for i in range(len(df["price"])):
                    if ((df["price"][i]["regular_price"]["value"]-df["price"][i]["offer_price"]["value"])==query["filters"][0]["operand2"]):
                        dis_summ+=(df["price"][i]["regular_price"]["value"]-df["price"][i]["offer_price"]["value"])
                        c+=1
            if query["filters"][0]["operator"]=="<":
                for i in range(len(df["price"])):
                    if ((df["price"][i]["regular_price"]["value"]-df["price"][i]["offer_price"]["value"])<query["filters"][0]["operand2"]):
                        dis_summ+=(df["price"][i]["regular_price"]["value"]-df["price"][i]["offer_price"]["value"])
                        c+=1
            avg_dis = dis_summ/c
            return jsonify({"discounted_products_count":c,"avg_dicount":avg_dis})

        if query["filters"][0]["operand1"]=="brand.name":
            for i in range(len(df["brand"])):
                if df["brand"][i]["name"]==query["filters"][0]["operand2"]:
                    dis_summ+=(df["price"][i]["regular_price"]["value"]-df["price"][i]["offer_price"]["value"])
                    c+=1
            avg_dis = dis_summ/c
            return jsonify({"discounted_products_count":c,"avg_dicount":avg_dis})

#3. NAP products where they are selling at a price higher than any of the competition.    
    if query["query_type"]=="expensive_list":
        # list to store ids of competitors site
        nap_id=[]
        #list to input NaN so not to encounter any error in future
        p=[]
        l1 = list(df["similar_products"].isna())
        for i in range(len(l1)):
            if l1[i] ==True:
                p.append(i)

        
        if "filters" in query:
            if query["filters"][0]["operand1"]=="brand.name" and query["filters"][0]["operator"]=="==":
                for i in range(len(df["price"])):
                    if df["brand"][i]["name"] == query["filters"][0]["operand2"] and (i not in p) and df["similar_products"][i]["meta"]["total_results"] >0:
                        for j in l:
                            if df["similar_products"][i]["website_results"][j]["knn_items"]!=[] and df["similar_products"][i]["website_results"][j]["knn_items"][0]["_source"]["price"]["basket_price"]["value"]<df["price"][i]["basket_price"]["value"]:
                                nap_id.append(str(df["_id"][i]))
                                break
            return jsonify({'expensive_list':nap_id})
        else:
            for i in range(len(df["price"])):
                if (i not in p) and df["similar_products"][i]["meta"]["total_results"] >0:
                    for j in l:
                        if df["similar_products"][i]["website_results"][j]["knn_items"]!=[] and df["similar_products"][i]["website_results"][j]["knn_items"][0]["_source"]["price"]["basket_price"]["value"]<df["price"][i]["basket_price"]["value"]:
                            nap_id.append(str(df["_id"][i]))
                            break
            return jsonify({'expensive_list':nap_id})

#4. NAP products where they are selling at a price n% higher than a competitor X.
    if query["query_type"]=="competition_discount_diff_list":
        #list to input NaN so not to encounter any error in future
        p=[]
        l1 = list(df["similar_products"].isna())
        for i in range(len(l1)):
            if l1[i] ==True:
                p.append(i)
        nap_id = []
        opr = query["filters"][0]["operand2"]
        opr2 = query["filters"][1]["operand2"]
        if query["filters"][0]["operator"]==">":
            for i in range(len(df["price"])):
                if (i not in p) and df["similar_products"][i]["website_results"][opr2]["knn_items"]!=[]:
                    comp_basket_price = df["similar_products"][i]["website_results"][opr2]["knn_items"][0]["_source"]["price"]["basket_price"]["value"]
                    if (((comp_basket_price*opr)/100)+comp_basket_price) < df["price"][i]["basket_price"]["value"] :
                        nap_id.append(str(df["_id"][i]))

        if query["filters"][0]["operator"]=="==":
            for i in range(len(df["price"])):
                if (i not in p) and df["similar_products"][i]["website_results"][opr2]["knn_items"]!=[]:
                    comp_basket_price = df["similar_products"][i]["website_results"][opr2]["knn_items"][0]["_source"]["price"]["basket_price"]["value"]
                    if (((comp_basket_price*opr)/100)+comp_basket_price) == df["price"][i]["basket_price"]["value"] :
                        nap_id.append(str(df["_id"][i]))

        if query["filters"][0]["operator"]=="<":
            for i in range(len(df["price"])):
                if (i not in p) and df["similar_products"][i]["website_results"][opr2]["knn_items"]!=[]:
                    comp_basket_price = df["similar_products"][i]["website_results"][opr2]["knn_items"][0]["_source"]["price"]["basket_price"]["value"]
                    if (((comp_basket_price*opr)/100)+comp_basket_price) > df["price"][i]["basket_price"]["value"] :
                        nap_id.append(str(df["_id"][i]))
        
        return jsonify({"competition_discount_diff_list":nap_id})

def init_files(dump_path = 'dumps/netaporter_gb.json'):
    if dump_path.split('/')[0] not in os.listdir():
        os.mkdir(dump_path.split('/')[0])
    if os.path.exists(dump_path):
        pass
    else:
        gdown.download(url = url, output = dump_path, quiet=False)

def prepare_dataset(path = 'dumps/netaporter_gb.json'):
    product_json=[]
    with open('dumps/netaporter_gb.json') as fp:
        for product in fp.readlines():
            product_json.append(json.loads(product))
    df=pd.read_json("dumps/netaporter_gb.json",lines=True,orient='columns')
    return df


# RUN FLASK APPLICATION
if __name__ == '__main__':
    '''MAKE SURE YOU HAVE 'gdown' LIBRARY IN YOUR 'requirements.txt' TO DOWNLOAD FILE FROM Gdrive.'''
    # RUNNNING FLASK APP
    app.run(debug=True, host = '0.0.0.0', port=5000)

    # GETTING DATASET this function will download the dataset
    init_files('dumps/netaporter_gb.json')

    # PREPARING DATASET
    df = prepare_dataset('dumps/netaporter_gb.json')
