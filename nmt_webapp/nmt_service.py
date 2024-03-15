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

import nemo.collections.nlp as nemo_nlp
from nemo.utils import logging
from utils import split_long_text

MODELS_DICT = {}

model = None
api = Flask(__name__)
CORS(api)

api.config['JSON_AS_ASCII'] = False

def initialize(config_file_path: str):
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
            MODELS_DICT[key] = model
    else:
        raise ValueError("Did not find the config.json or it was empty")
    logging.info("NMT service started")


@api.route('/translate', methods=['GET'])
def get_translation():
    try:
        time_s = time.time()
        max_length = 256       
        langpair = request.args["langpair"]
        if "zh-" in langpair or "jp-" in langpair:
            period_char = "。"
        else:
            period_char = "."
        src = request.args["text"]
        do_moses = request.args.get('do_moses', False)
        if langpair in MODELS_DICT:
            # deal with long source text            
            if do_moses:
                if len(src) <= max_length:
                    results = MODELS_DICT[langpair].translate(
                        [src], source_lang=langpair.split('-')[0], target_lang=langpair.split('-')[1]
                    )
                else:
                    passages = split_long_text(src, max_length=max_length, period_char=period_char)
                    
                    results = MODELS_DICT[langpair].translate(
                    passages, source_lang=langpair.split('-')[0], target_lang=langpair.split('-')[1])
            else:
                if len(src) <= max_length:
                    results = MODELS_DICT[langpair].translate([src])
                else:
                    passages = split_long_text(src, max_length=max_length, period_char=period_char)
                    results = MODELS_DICT[langpair].translate(passages)
            
            # combine translated text
            translated_text = ''.join(results)

            duration = time.time() - time_s
            logging.info(
                f"Translated in {duration}. Input was: {request.args['text']} <############> Translation was: {translated_text}"
            )
            res = {'translation': translated_text}
            response = flask.jsonify(res, )
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

        else:
            logging.error(f"Got the following langpair: {langpair} which was not found")
    except Exception as ex:
        res = {'translation': str(ex)}
        response = flask.jsonify(res)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return res


if __name__ == '__main__':
    initialize('config.json')
    api.run(host='0.0.0.0')
