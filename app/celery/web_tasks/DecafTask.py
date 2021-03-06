__author__ = 'parallels'
import sys
path = '/home/ubuntu/cloudcv/cloudcv17'
sys.path.append(path)

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cloudcv17.settings")

import json
from urlparse import urlparse
import traceback
import os
import os.path
import redis
from app.log import log, log_to_terminal, log_error_to_terminal, log_and_exit
import app.executable.decaf_cal_feature as decaf
import caffe
import app.conf as conf

r = redis.StrictRedis(host='cloudcv.org', port=6379, db=0)

from app.celery.celery.celery import celery

@celery.task
def decafImages(src_path, output_path, socketid, result_path, single_file_name='', modelname=''):
    if modelname is not '':
        lMODEL_FILE = str(os.path.join(conf.CAFFE_DIR, 'models',modelname,'deploy.prototxt'))
        lPRETRAINED = str(os.path.join(conf.CAFFE_DIR, 'models', modelname, modelname+'.caffemodel'))
        r.publish('chat', json.dumps({'error': lMODEL_FILE+'   '+lPRETRAINED, 'socketid': socketid}))
        caffe.set_phase_test()
        caffe.set_mode_gpu()
        modelnet = caffe.Classifier(lMODEL_FILE, lPRETRAINED)
        #r.publish('chat', json.dumps({'error': str(modelname), 'socketid': socketid}))

    else:
        modelnet = None

    try:
        #Entire Directory
        if os.path.isdir(os.path.join(src_path,single_file_name)):

            for file_name in os.listdir(src_path):
                tags = {}
                image_path = os.path.join(src_path, file_name)
                if os.path.isfile(image_path):

                    """ Trying to get the output of classify python script to send to user - Part 1/4
                    myPrint = CustomPrint(socketid)
                    old_stdout=sys.stdout
                    sys.stdout = myPrint
                    """
                    print 'Running caffe classify on multiple images'

                    mat_file_path = decaf.calculate_decaf_image(file_name, src_path, output_path, 3, socketid, tags, modelname, modelnet)
                    print tags
                    """ Part 2/2
                    sys.stdout=old_stdout
                    """
                    log_to_terminal("Results: "+str(tags), socketid)
                    # sorted_tags = sorted(tags.iteritems(), key=operator.itemgetter(1), reverse=True)

                    # webResult = {}
                    #webResult[str(result_path + file_name)] = sorted_tags
                    result_url = urlparse(result_path).path
                    r.publish('chat',
                                   json.dumps({'web_result': os.path.join(result_url, 'results', file_name+'.mat'), 'socketid': str(socketid)}))

            log_to_terminal('Thank you for using CloudCV', socketid)
        # Single File
        else:
            """ Part 3/4
            myPrint = CustomPrint(socketid)
            old_stdout=sys.stdout
            sys.stdout = myPrint
            """
            tags = {}
            print 'Running caffe classify on a single image: ' + single_file_name

            mat_file_path = decaf.calculate_decaf_image(single_file_name, src_path, output_path, 3, socketid, tags, modelname, modelnet)
            """ Part 4/4
            sys.stdout=old_stdout
            """
            log_to_terminal("Results: "+str(tags), socketid)

            # tags = sorted(tags.iteritems(), key=operator.itemgetter(1), reverse=True)
            # web_result = {}
            # web_result[str(result_path)] = tags
            result_url = os.path.dirname(urlparse(result_path).path)
            r.publish('chat', json.dumps({'web_result': os.path.join(result_url, 'results', single_file_name+'.mat'), 'socketid': str(socketid)}))

            log_to_terminal('Thank you for using CloudCV', socketid)

    except Exception as e:
        log_to_terminal(str(traceback.format_exc()), socketid)
