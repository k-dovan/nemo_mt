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
from utils import split_long_text, split_long_text_by_sentence_and_quotation, replace_doi_terms, remove_troll_characters

from nmt_multi import My_NMT_T2TT
from nmt_en2vi import translate_en2vi

# save both nemo and seamlessM4T models
NEMO_MODELS_DICT = {}

# declare seamless multi-model
nmt_multi_model = None
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

def init_nmt_multi():
    global nmt_multi_model
    nmt_multi_model = My_NMT_T2TT()

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

def merge_english_chunks(translated_en_paragraphs: list, ext_characters: list):
    merged_paragraphs = []
    merged_ext_characters = []
    cur_paragraph = ""
    last_ext_character = ""
    for p,ext in zip(translated_en_paragraphs, ext_characters):
        if p.strip() != "" and (last_ext_character.strip() == "," or last_ext_character.startswith("\"")):
            p = p[0].lower() + p[1:]
        if ext.strip() == ".":
            cur_paragraph += (p.strip() + ext.strip())
            merged_paragraphs.append(cur_paragraph)
            # make empty list of ext_characters to have the same structure
            # as not merging english chunks
            merged_ext_characters.append(' ') 
            cur_paragraph = ""
        else:
            cur_paragraph += (p.strip() + ext)
        
        last_ext_character = ext
    # check very last chunk
    if cur_paragraph.strip() != "":
        merged_paragraphs.append(cur_paragraph.strip())
        # make empty list of ext_characters to have the same structure 
        # as not merging english chunks
        merged_ext_characters.append('')
    
    return merged_paragraphs, merged_ext_characters

def translate(src_text: str, langpair: str, 
              merge_en_chunks: bool = True, 
              replace_doi_terms: bool = True,
              translate_by_sentence: bool = True, 
              max_length: int = 64):
    
    source_lang = langpair.split('-')[0]
    target_lang = langpair.split('-')[1]

    # whether to merge english chunks before translating from en to vi
    is_merge_english_chunks = merge_en_chunks
    # translate by sentence or by chunk of texts
    is_translate_by_sentence = translate_by_sentence
    
    time_s = time.time()
    max_length = max_length

    # remove troll characters from text if exists
    src_text = remove_troll_characters(src_text)

    # ---------------------------------------------
    # replace special terms for given language
    # ---------------------------------------------
    if replace_doi_terms:
        src_text = replace_doi_terms(src_text, lang=source_lang)

    print ("replaced src text:", src_text)

    if source_lang == "zh":
        period_char = "。"
        comma_char = "，"
        open_quotes: str =  '“‘『「'
        close_quotes: str = '”’』」'
    elif source_lang == "jp":
        period_char = "。"
        comma_char = "，"
        open_quotes: str =  '“‘『「'
        close_quotes: str = '”’』」'
    elif source_lang == "km":
        period_char = "។"
        comma_char = ","
        open_quotes: str =  '«“'
        close_quotes: str = '»”'
    elif source_lang == "lo":
        period_char = "."
        comma_char = ","
        open_quotes: str =  '“'
        close_quotes: str = '”'
    else:
        period_char = "."
        comma_char = ","
        open_quotes: str =  '"'
        close_quotes: str = '"'
    
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
    elif langpair in SEAMLESS_SUPPORTED_LANG_PAIRS:
        mt_model = nmt_multi_model
    else:
        logging.error(f"Got the following langpair: {langpair} which was not found")

    if mt_model is not None:

        # if there's no text to translate
        if len(src_text.strip()) == 0:
            return write_response("")
        
        if not is_translate_by_sentence:
            # deal with long source text
            # bool array `paragaph_flags` with same length as `passages` array 
            # indicating if passage at index `i` of `passages` finishes current paragraph
            # and the next passage will belong to a new paragraph
            paragraphs, ext_characters = split_long_text(src_text, 
                                                         max_length=max_length, 
                                                         period_char=period_char)
        else:
            paragraphs, ext_characters = split_long_text_by_sentence_and_quotation(
                                                long_text=src_text, 
                                                period_char=period_char,
                                                comma_char=comma_char,
                                                open_quotes=open_quotes,
                                                close_quotes=close_quotes)

        # print ('>>> paragraphs splitted: ', paragraphs)
        logging.info(f"paragraphs: {paragraphs}")
        logging.info(f"ext_characters: {ext_characters}")
        
        # same interface for both nemo and seamless models
        # due to missing translation with batch translation 
        # we translate single paragraph at a time and combine them
        translated_paragraphs = []
        for p in paragraphs:
            if p.strip() == "":
                translated_p = [""]
            else:
                translated_p = mt_model.translate([p],
                                        source_lang=source_lang, 
                                        target_lang=target_lang)
            
            # clean punctuations and quotations
            translated_p[0] = translated_p[0].strip('." ')
            
            translated_paragraphs.extend(translated_p)            

        logging.info(f"translated_paragraphs: {translated_paragraphs}")
        
        # check if we need to translate to vi
        if use_en2vi:
            if is_merge_english_chunks:
                translated_paragraphs, ext_characters = merge_english_chunks(translated_paragraphs, ext_characters)

                print ("> After merging, translated_paragraphs: ", translated_paragraphs)

            translated_to_vi_paragraphs = []
            for p in translated_paragraphs: 
                if p.strip() == "":
                    translated_p = [""]
                else:
                    translated_p = translate_en2vi([p])
                
                if not is_merge_english_chunks:
                    # clean punctuations and quotations
                    translated_p[0] = translated_p[0].strip('." ')

                translated_to_vi_paragraphs.extend(translated_p)
            translated_paragraphs = translated_to_vi_paragraphs

            logging.info(f"translated_to_vi_paragraphs: {translated_to_vi_paragraphs}")

        translated_text = ""
        last_ext_chr = ""
        comma_en = ","
        for text, ext_chr in zip(translated_paragraphs, ext_characters): 
            # if text.strip() != "" and last_ext_chr.strip() == comma_en:
            #     text = text[0].lower() + text[1:]               
            translated_text += (text.strip() + ext_chr)
            last_ext_chr = ext_chr

        # strip last space character
        translated_text = translated_text.strip()

        duration = time.time() - time_s
        logging.info(
            f"Translated in {duration}\nInput was: {src_text}\nTranslation was: {translated_text}"
        )

        # try to free cache if necessary
        free_cache()

        return translated_text
    else:
        return f"Got the following langpair: {langpair} which was not found."

@api.route('/translate', methods=['GET'])
def get_translation():
    try:
        src_text = request.args["text"]   
        langpair = request.args["langpair"]
        
        translated_text = translate(src_text, langpair, 
                                    replace_doi_terms=False,
                                    merge_en_chunks=False,
                                    translate_by_sentence=False,
                                    max_length=64)
        
        return write_response(translated_text)
        
    except Exception as ex:
        return write_response(ex)

if __name__ == '__main__':
    init_nemo('config.json')
    init_nmt_multi()
    serve(api, host="0.0.0.0", port=5000)
