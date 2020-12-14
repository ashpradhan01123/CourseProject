import sys
import os
import json 
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask,jsonify
from flask import make_response, request, current_app
from functools import update_wrapper
from datetime import timedelta
from flask_socketio import SocketIO
from bs4 import BeautifulSoup
import requests
import requests.exceptions
from urllib.parse import urlsplit
import urllib
import urllib.request
from collections import deque
import pandas as pd
import re
import csv
import lxml
import os
from PyPDF2 import PdfFileWriter, PdfFileReader

app = Flask(__name__, instance_relative_config=True)

app.secret_key =b'\xaa\x12\xce\xdf\xc3\xb1\x90\xd8!z\xe6\xe9V\x82<r'
parent_dir = ""
subject_list = ["ece-313","cs-554","cs-425"]
subject_dir = "./pdf.js/static/slides/"
subject_name = ""
processed_urls = set()
local_urls = set()
foreign_urls = set()
broken_urls = set()
subject_url = ["https://courses.engr.illinois.edu/ece313/sp2013/Slides.html","https://solomonik.cs.illinois.edu/teaching/cs554/index.html","https://courses.engr.illinois.edu/cs425/fa2019/lectures.html"]

srv_url = 'http://timan102.cs.illinois.edu/explanation/'
# app.config.from_object('config')

socketio = SocketIO(app) 
application = app

from flask import render_template
from flask import request,jsonify,session
import urllib
import model
# import forms
import datetime

COURSE_NAMES = None
NUM_COURSES = None
NUM_VIS = 0
MAX_HIST = 50
m = 0
n = 0
IS_LOCAL_SRV = True 


def crossdomain(origin=None, methods=None, headers=None, max_age=21600,
                attach_to_all=True, automatic_options=True):
    """Decorator function that allows crossdomain requests.
      Courtesy of
      https://blog.skyred.fi/articles/better-crossdomain-snippet-for-flask.html
    """
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    # use str instead of basestring if using Python 3.x
    if headers is not None and not isinstance(headers, str):
        headers = ', '.join(x.upper() for x in headers)
    # use str instead of basestring if using Python 3.x
    if not isinstance(origin, str):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        """ Determines which methods are allowed
        """
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        """The decorator function
        """
        def wrapped_function(*args, **kwargs):
            """Caries out the actual cross domain code
            """
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers
            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            h['Access-Control-Allow-Credentials'] = 'true'
            h['Access-Control-Allow-Headers'] = \
                "Origin, X-Requested-With, Content-Type, Accept, Authorization"
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

def get_prev_urls():
    global NUM_VIS
    try:
        prev_urls = session['urls']
        # print ("prev",prev_urls,session['disp_strs'])
        NUM_VIS = len(prev_urls)
    except KeyError:
        session['urls'] = []
        session['disp_strs'] = []
        session.modified = True
        NUM_VIS = 0
    return list(session['urls']),list(session['disp_strs'])

def create_dir(directory):
    try:
        os.mkdir(directory)
    except OSError as error:
        print(error)

def split_pdf_file(dir_name,pdffile, lecture_name):
    pathforpdf = parent_dir + dir_name + '/'

    try:
        for filename in os.listdir(pathforpdf):
            if filename.endswith('.pdf'):
                pdfreaderobj = open(pathforpdf + filename, "rb")
                inputpdf = PdfFileReader(pdfreaderobj)

                for i in range(inputpdf.numPages):
                    output = PdfFileWriter()
                    output.addPage( inputpdf.getPage(i))
                    pdfwritererobj = pathforpdf + "%s----%s----%s----%s.txt----slide%s.pdf" % (subject_name, dir_name, dir_name, lecture_name, i)
                    outputStream = open(pdfwritererobj, "wb")
                    output.write(outputStream)
                    outputStream.close()
                pdfreaderobj.close()
        os.remove(pathforpdf + filename)
    except OSError as error:
        #print(error)
        pdfreaderobj.close()
        os.remove(pathforpdf + filename)
        os.rmdir(pathforpdf)
        #print(error)


def download_file(download_url, dir_name, pdffile, lecture_Name):
    try:
        response = urllib.request.urlopen(download_url)
        pdffilepath = parent_dir[2:] + dir_name + "/" + pdffile
        file = open(pdffilepath,'wb')
        file.write(response.read())
        file.close()
        split_pdf_file(dir_name, pdffile, lecture_Name)

    except urllib.error.HTTPError as e:
        os.rmdir(parent_dir[2:] + dir_name + "/")
        #print(e)

def crawlsubject():
    global subject_name
    global parent_dir
    m=0
    n=0
    for index in range(len(subject_list)):
        subject_name = subject_list[index]
        url = subject_url[index]
        parent_dir = subject_dir + subject_name + '/'
        if os.path.exists(parent_dir) == False:
            create_dir(parent_dir)
            new_urls = deque([url])
            while len(new_urls):
                url = new_urls.popleft()
                processed_urls.add(url)

                if ((url.endswith(".pdf") == False) and (url.endswith(".jpg") == False) and (
                        url.endswith(".zip") == False) and (url.endswith(".mp4") == False) and (
                        url.endswith(".ppt") == False) and (url.endswith(".pptx") == False)):
                    try:
                        response = requests.get(url, allow_redirects=False)
                    except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError,
                            requests.exceptions.InvalidURL,
                            requests.exceptions.InvalidSchema):
                        broken_urls.add(url)
                        continue
                    parts = urlsplit(url)
                    base = "{0.netloc}".format(parts)
                    strip_base = base.replace("www.", "")
                    base_url = "{0.scheme}://{0.netloc}".format(parts)
                    path = url[:url.rfind('/') + 1] if '/' in parts.path else url
                    soup = BeautifulSoup(response.text, 'lxml')

                    # find subject name
                    if ('cs425' in url):
                        title_name = soup.title.string
                        if ('Lectures' in title_name):
                            table = soup.find(
                                lambda tag: tag.name == 'table' and tag.has_attr('id') and tag['id'] == "Table3")
                            if (table):
                                df = pd.read_html(str(table), header=0)[0]
                                df.columns = df.columns.str.strip()
                                df.columns = df.columns.map(
                                    lambda x: x.replace("-", "_").replace(" ", "_").replace(",", "_"))
                                df.columns = df.columns.map(lambda x: x.replace("#", 'No'))

                    if ('cs554' in url):
                        title_name = soup.title.string
                        print(title_name)
                        table = soup.find('table')

                        if (table):
                            df = pd.read_html(str(table))[0]
                            df.columns = ["Chapter", "Notes", "Section", "Slides", "Video"]
                            df.columns = df.columns.str.strip()
                            df.columns = df.columns.map(
                                lambda x: x.replace("-", "_").replace(" ", "_").replace(",", "_"))
                            df.columns = df.columns.map(lambda x: x.replace("#", 'No'))

                    if ('ece313' in url):
                        m = m + 1
                        m, n = 2, 55;
                        Ece_Details = [[0] * m for i in range(n)]
                        i = 0
                        for i, tag in enumerate(soup.find_all("li")):
                            str1 = tag.text
                            Lect_Details = str1.split(':')
                            Ece_Details[i][0] = Lect_Details[0]
                            Ece_Details[i][1] = Lect_Details[1].strip()

                    for link in soup.find_all('a'):
                        anchor = link.attrs["href"] if "href" in link.attrs else ''
                        if anchor.startswith('/'):
                            local_link = base_url + anchor
                            local_urls.add(local_link)
                        elif strip_base in anchor:
                            local_urls.add(anchor)
                        elif not anchor.startswith('http'):
                            local_link = path + anchor
                            local_urls.add(local_link)
                        else:
                            foreign_urls.add(anchor)

                        for i in local_urls:
                            if not i in new_urls and not i in processed_urls:
                                new_urls.append(i)

                if (url.endswith(".pdf")):
                    lastres = url.rfind('/')
                    Lecpdf = url[lastres + 1:]
                    LectDir = Lecpdf[:len(Lecpdf) - 4]
                    if 'Intro' in LectDir:
                        LectDir = 'Lecture00'
                    if 'poster' not in LectDir and (LectDir.startswith('L') or LectDir.startswith('slide')):
                        if LectDir.startswith('L') and (LectDir.endswith('.FA19') or '.FA19' in LectDir):
                            if ('last' in LectDir):
                                Lect_No = 29
                            else:
                                Lect_No = LectDir[1:LectDir.index('.')]

                                if (Lect_No.find("-") != -1):
                                    Lect_No = LectDir[1:LectDir.index('-')]
                            for ind in df.index:
                                df_Lect_No = df["Lecture_No"][ind]
                                if (float(Lect_No) == df_Lect_No):
                                    Lecture_Name1 = df["Lecture_Name"][ind]
                                    print(Lecture_Name1, Lect_No)
                            LectDir = LectDir.replace('.FA19', '')
                            LectDir = LectDir.replace('L', 'Lecture')
                        elif LectDir.startswith('slide'):
                            Lect_No = LectDir[LectDir.index('_') + 1:]
                            Lecture_Name1 = df.Section[float(Lect_No) - 1]
                            LectDir = LectDir.replace('slides', 'Lecture')
                        elif LectDir.startswith('Lecture'):
                            Lect_No = LectDir[7:]
                            Lect_No_1 = int(Lect_No)
                            Lecture_Name1 = Ece_Details[Lect_No_1][1]
                            Lecture_Name1 = Lecture_Name1.replace('\r\n',' ')
                            Lecture_Name1 = Lecture_Name1.replace('\n', ' ')
                            Lecture_Name1 = Lecture_Name1.replace('?', '')

                        lecture_name = Lecture_Name1.replace('/','_')
                        create_dir(parent_dir + LectDir)
                        download_file(url, LectDir, Lecpdf, lecture_name)

def set_sess(url,ses_disp_str):
    global MAX_HIST,IS_LOCAL_SRV
    if not IS_LOCAL_SRV:

        url = modify_url_domain(url)
    if (len(session['urls'])==0) or (len(session['urls'])>0 and session['urls'][-1]!=url): #consecutive visits to same slide
        if len(session['urls']) == MAX_HIST:
            session['urls'].pop(0)
            session['disp_strs'].pop(0)
        session['urls'].append(url)
        session['disp_strs'].append(ses_disp_str)
        session.modified = True

def modify_url_domain(url):
    return url.replace('http://localhost:8096/','http://timan102.cs.illinois.edu/explanation//')

@app.route('/')
def index():
    global COURSE_NAMES,NUM_COURSES,NUM_VIS
    COURSE_NAMES,NUM_COURSES = model.get_course_names()
    model.load_related_slides()
    vis_urls,vis_strs = get_prev_urls()

    return render_template("base.html",course_names=COURSE_NAMES,num_courses=NUM_COURSES,vis_urls=vis_urls,vis_strs=vis_strs,num_vis=NUM_VIS)

def resolve_slide(course_name,lno,type_,slide_name=None,log=False,action=None):
    global COURSE_NAMES,NUM_COURSES
    if COURSE_NAMES is None and NUM_COURSES is None:
        COURSE_NAMES,NUM_COURSES = model.get_course_names()
    if type_ =='drop-down':
        ret = model.get_next_slide(course_name,lno)
    elif type_ == 'related' or type_=='search_results':
        ret = model.get_slide(course_name,slide_name,lno)
    elif type_ == 'next':
        ret = model.get_next_slide(course_name,lno,slide_name)
    elif type_ == 'prev':
        ret = model.get_prev_slide(course_name,lno,slide_name)
    if log:
        if ret[0] is not None:
            print ('logging ', ret[0])
            model.log(request.remote_addr,ret[0],datetime.datetime.now(),action)
        else:
            model.log(request.remote_addr,'End',datetime.datetime.now(),action)
    return ret

@app.route('/slide/<course_name>/<lno>')
def slide(course_name,lno):
    global NUM_VIS
    next_slide_name,lno,lec_name,(num_related_slides,related_slides,disp_str,related_course_names,rel_lnos,rel_lec_names,disp_color,disp_snippet),lec_names,lnos,ses_disp_str= resolve_slide(course_name,lno,'drop-down')
    vis_urls,vis_strs = get_prev_urls()

    if next_slide_name is not None:
        set_sess(request.url,ses_disp_str)

    return render_template("slide.html",slide_name=next_slide_name,course_name=course_name,num_related_slides=num_related_slides,related_slides = related_slides,disp_str=disp_str,disp_color=disp_color,disp_snippet=disp_snippet,related_course_names=related_course_names,lno=lno,lec_name=lec_name,lec_names=lec_names,lnos=lnos,course_names=COURSE_NAMES,num_courses=NUM_COURSES,rel_lnos=rel_lnos,rel_lec_names=rel_lec_names,vis_urls=vis_urls,vis_strs=vis_strs,num_vis=NUM_VIS)



@app.route('/related_slide/<course_name>/<lno>/<slide_name>')
def related_slide(course_name,slide_name,lno):
    global NUM_VIS
    next_slide_name,lno,lec_name,(num_related_slides,related_slides,disp_str,related_course_names,rel_lnos,rel_lec_names,disp_color,disp_snippet),lec_names,lnos,ses_disp_str=resolve_slide(course_name,lno,'related',slide_name=slide_name)
    vis_urls,vis_strs = get_prev_urls()

    if next_slide_name is not None:
        set_sess(request.url,ses_disp_str)

    return render_template("slide.html",slide_name=next_slide_name,course_name=course_name,num_related_slides=num_related_slides,related_slides = related_slides,disp_str=disp_str,disp_color=disp_color,disp_snippet=disp_snippet,related_course_names=related_course_names,lno=lno,lec_name=lec_name,lec_names=lec_names,lnos=lnos,course_names=COURSE_NAMES,num_courses=NUM_COURSES,rel_lnos=rel_lnos,rel_lec_names=rel_lec_names,vis_urls=vis_urls,vis_strs=vis_strs,num_vis=NUM_VIS)



@app.route('/next_slide/<course_name>/<lno>/<curr_slide>')
def next_slide(course_name,lno,curr_slide):
    global NUM_VIS
    next_slide_name,lno,lec_name,(num_related_slides,related_slides,disp_str,related_course_names,rel_lnos,rel_lec_names,disp_color,disp_snippet),lec_names,lnos,ses_disp_str = resolve_slide(course_name,lno,'next',slide_name=curr_slide)

    vis_urls,vis_strs = get_prev_urls()


    if next_slide_name is not None:
        set_sess(request.url,ses_disp_str)


    if next_slide_name is not None:
        return render_template("slide.html",slide_name=next_slide_name,course_name=course_name,num_related_slides=num_related_slides,related_slides = related_slides,disp_str=disp_str,disp_color=disp_color,disp_snippet=disp_snippet,related_course_names=related_course_names,lno=lno,lec_name=lec_name,lec_names=lec_names,lnos=lnos,course_names=COURSE_NAMES,num_courses=NUM_COURSES,rel_lnos=rel_lnos,rel_lec_names=rel_lec_names,vis_urls=vis_urls,vis_strs=vis_strs,num_vis=NUM_VIS )
    else:
        return render_template("end.html",course_names=COURSE_NAMES,num_courses=NUM_COURSES,vis_urls=vis_urls,vis_strs=vis_strs,num_vis=NUM_VIS)

@app.route('/prev_slide/<course_name>/<lno>/<curr_slide>')
def prev_slide(course_name,lno,curr_slide):
    global NUM_VIS
    prev_slide_name,lno,lec_name,(num_related_slides,related_slides,disp_str,related_course_names,rel_lnos,rel_lec_names,disp_color,disp_snippet),lec_names,lnos,ses_disp_str=resolve_slide(course_name,lno,'prev',slide_name=curr_slide)

    vis_urls,vis_strs = get_prev_urls()

    if prev_slide_name is not None:
        set_sess(request.url,ses_disp_str)

    if prev_slide_name is not None:
        return render_template("slide.html",slide_name=prev_slide_name,course_name=course_name,num_related_slides=num_related_slides,related_slides = related_slides,disp_str=disp_str,disp_color=disp_color,disp_snippet=disp_snippet,related_course_names=related_course_names,lno=lno,lec_name=lec_name,lec_names=lec_names,lnos=lnos,course_names=COURSE_NAMES,num_courses=NUM_COURSES,rel_lnos=rel_lnos,rel_lec_names=rel_lec_names,vis_urls=vis_urls,vis_strs=vis_strs,num_vis=NUM_VIS)
    else:
        return render_template("end.html",course_names=COURSE_NAMES,num_courses=NUM_COURSES,vis_urls=vis_urls,vis_strs=vis_strs,num_vis=NUM_VIS)


@app.route('/end')
def end():
    global COURSE_NAMES,NUM_COURSES,NUM_VIS
    if COURSE_NAMES is None and NUM_COURSES is None:
        COURSE_NAMES,NUM_COURSES = model.get_course_names()
    vis_urls,vis_strs = get_prev_urls()
    return render_template("end.html",course_names=COURSE_NAMES,num_courses=NUM_COURSES,vis_urls=vis_urls,vis_strs=vis_strs,num_vis=NUM_VIS)

@socketio.on('connect')
def value_changed():
    print("connected")


@app.route('/explain', methods=['POST','OPTIONS'])
@crossdomain(origin='*')
def socket_connection(course_name=None, lno=None, slide_name=None, curr_slide=None):

    search_string = request.json['searchString']
    socketio.emit('message', search_string,broadcast=True)
    print(request,search_string)
    # model.log(request.remote_addr,search_string,datetime.datetime.now(),'search_query')
    # num_results,results,disp_strs,search_course_names,lnos, snippets,lec_names = model.get_search_results(search_string)
    # if not results:
    # 	num_results = 0
    # 	results = []

    return 'OK'

@app.route('/search', methods=['POST'])
def results(course_name=None, lno=None, slide_name=None, curr_slide=None):   
    data = json.loads(request.data.decode('utf-8'))
    # print(1,1,data)
    querytext = data['searchString']
    explanation,file_names = model.get_explanation(querytext)
    if explanation == '':
        num_results = 0
    else:
        num_results = 1
    response = jsonify({ 'num_results': num_results, 'explanation':explanation,'file_names':file_names})
    # print(response)
    return response

@app.route('/search_slide/<course_name>/<lno>/<slide_name>')
def search_slide(course_name,slide_name,lno):
    return related_slide(course_name,slide_name,lno)

@app.route('/search_slides', methods=['POST'])
def search_results(course_name=None, lno=None, slide_name=None, curr_slide=None):
    search_string = request.json['searchString']
    log_helper(search_string + '###QUERY',request.json['route'])

    num_results,results,disp_strs,search_course_names,lnos, snippets,lec_names = model.get_search_results(search_string)
    if not results:
        num_results = 0
        results = []
    response = jsonify({ 'num_results': num_results, 'results':results, 'disp_strs':disp_strs, 'search_course_names':search_course_names,'lnos':lnos,'course_names':COURSE_NAMES,'num_courses':NUM_COURSES,'snippets':snippets,'lec_names':lec_names
    })
    return response

def log_helper(action,route):
    if action is not None and route is not None:
        route_ele = route.split('/')
        if IS_LOCAL_SRV:
            func_type = route_ele[1]
        else:
            func_type = route_ele[3]
        print (func_type,route_ele)
        if IS_LOCAL_SRV:
            beg = 2
        else:
            beg = 4
        if func_type == 'related_slide':
            resolve_slide(route_ele[beg],route_ele[beg+1],'related',slide_name=route_ele[beg+2],log=True,action=action)
        elif func_type == 'next_slide':
            resolve_slide(route_ele[beg],route_ele[beg+1],'next',slide_name=route_ele[beg+2],log=True,action=action)
        elif func_type == 'prev_slide':
            resolve_slide(route_ele[beg],route_ele[beg+1],'prev',slide_name=route_ele[beg+2],log=True,action=action)
        elif func_type == 'slide':
            resolve_slide(route_ele[beg],route_ele[beg+1],'drop-down',log=True,action=action)
        elif func_type == 'search_slide':
            resolve_slide(route_ele[beg],route_ele[beg+1],'search_results',slide_name=route_ele[beg+2],log=True,action=action)

@app.route('/log_action',methods=['GET', 'POST'])
def log_action():
    request_dict = json.loads(request.data)
    action = request_dict['action']
    route = request_dict['route']
    log_helper(action,route)
    resp = jsonify(success=True)

    return resp

def main():
    crawlsubject()
    socketio.run(app, host='localhost', port=8096)
if __name__ == '__main__':
    main()