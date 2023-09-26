# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import time

import flask
import torch
from flask import Flask, json, request
from flask_cors import CORS
from waitress import serve

import nemo.collections.nlp as nemo_nlp
from nemo.utils import logging
from utils import split_long_text

from seamless_m4t import MySeamlessT2TT
from nmt_en2vi import translate_en2vi

# save both nemo and seamlessM4T models
NEMO_MODELS_DICT = {}

# declare seamless multi-model
seamless_model = None
# seamless supported language pairs
SEAMLESS_SUPPORTED_LANG_PAIRS = ["km-en"]

model = None
api = Flask(__name__)
CORS(api)

api.config['JSON_AS_ASCII'] = False

def init_nemo(config_file_path: str):
    """
    Loads 'language-pair to NMT model mapping'
    """
    __MODELS_DICT = None

    logging.info("Starting NMT service")
    logging.info(f"I will attempt to load all the models listed in {config_file_path}.")
    logging.info(f"Edit {config_file_path} to disable models you don't need.")
    if torch.cuda.is_available():
        logging.info("CUDA is available. Running on GPU")
    else:
        logging.info("CUDA is not available. Defaulting to CPUs")

    # read config
    with open(config_file_path) as f:
        __MODELS_DICT = json.load(f)

    if __MODELS_DICT is not None:
        for key, value in __MODELS_DICT.items():
            logging.info(f"Loading model for {key} from file: {value}")
            if value.startswith("NGC/"):
                model = nemo_nlp.models.machine_translation.MTEncDecModel.from_pretrained(model_name=value[4:])
            else:
                model = nemo_nlp.models.machine_translation.MTEncDecModel.restore_from(restore_path=value)
            if torch.cuda.is_available():
                model = model.cuda()
            NEMO_MODELS_DICT[key] = model
    else:
        raise ValueError("Did not find the config.json or it was empty")
    logging.info("NMT service started")

def init_seamless_m4t():
    global seamless_model
    seamless_model = MySeamlessT2TT()

def write_response(content: str):
    res = {'translation': content}
    response = flask.jsonify(res, )
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

def free_cache(used_thresh: int = 0.5):
    # delete cache data from GPU if the used memory larger than 50% out of total
    memory_info = torch.cuda.mem_get_info()
    free = memory_info[0]
    total = memory_info[1]

    if free/total < used_thresh:
        torch.cuda.empty_cache()

@api.route('/translate', methods=['GET'])
def get_translation():
    try:
        time_s = time.time()
        max_length = 256 
        
        src = request.args["text"]   
        langpair = request.args["langpair"]
        source_lang = langpair.split('-')[0]
        target_lang = langpair.split('-')[1]

        if source_lang == "zh" or source_lang == "jp":
            period_char = "。"
        else:
            period_char = "."
        
        use_en2vi = False
        if target_lang == "vi":
            use_en2vi = True
            # update langpair to `-en`
            langpair = f'{source_lang}-en'
            target_lang = 'en'

        # set mt model
        mt_model = None
        if langpair in NEMO_MODELS_DICT:
            mt_model = NEMO_MODELS_DICT[langpair]
        # elif langpair in SEAMLESS_SUPPORTED_LANG_PAIRS:
        #     mt_model = seamless_model
        else:
            logging.error(f"Got the following langpair: {langpair} which was not found")

        if mt_model is not None:

            # if there's no text to translate
            if len(src.strip()) == 0:
                return write_response("")
            
            # deal with long source text
            # bool array `paragaph_flags` with same length as `passages` array 
            # indicating if passage at index `i` of `passages` finishes current paragraph
            # and the next passage will belong to a new paragraph
            paragraphs, ext_characters = split_long_text(src, max_length=max_length, period_char=period_char)

            # print ('>>> paragraphs splitted: ', paragraphs)
            
            # same interface for both nemo and seamless models
            # due to missing translation with batch translation 
            # we translate single paragraph at a time and combine them
            translated_paragraphs = []
            for p in paragraphs:
                translated_paragraphs.extend(mt_model.translate([p],
                                        source_lang=source_lang, 
                                        target_lang=target_lang
                                        ))
            
            # check if we need to translate to vi
            if use_en2vi:
                translated_paragraphs = translate_en2vi(translated_paragraphs)

            # print ('>>> paragraphs translated: ', translated_paragraphs)

            translated_text = ""
            for text, ext_chr in zip(translated_paragraphs, ext_characters):                
                translated_text += (text + ext_chr)
            # strip last space character
            translated_text = translated_text.strip()

            duration = time.time() - time_s
            logging.info(
                f"Translated in {duration}. Input was: {request.args['text']} <############> Translation was: {translated_text}"
            )

            # try to free cache if necessary
            free_cache()

            return write_response(translated_text)
        
    except Exception as ex:
        return write_response(ex)

if __name__ == '__main__':
    init_nemo('config.json')
    # init_seamless_m4t()
    serve(api, host="0.0.0.0", port=5000)
