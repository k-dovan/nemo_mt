# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
import torch
import random
import csv
import numpy as np
from seamless_communication.inference import Translator
from typing import List

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s -- %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# language mapping from common-language-code format to seamless-language-code format
LANGUAGE_MAP = {
    "en": "eng",
    "ru": "rus",
    "fr": "fra",
    "km": "khm",
    "lo": "lao",
    "th": "tha"
}

class My_NMT_T2TT:
    def __init__(self, model_name: str = "seamlessM4T_medium"):

        if torch.cuda.is_available():
            device = torch.device("cuda:0")
            dtype = torch.float16
            logger.info(f"Running inference on the GPU in {dtype}.")
        else:
            device = torch.device("cpu")
            dtype = torch.float32
            logger.info(f"Running inference on the CPU in {dtype}.")
    
        self.translator = Translator(
                            model_name_or_card=model_name,
                            vocoder_name_or_card="vocoder_36langs",
                            device=device,
                            dtype=dtype
                        )
    
    def translate(self, inputs: List[str], source_lang: str = "km", target_lang: str = "en"):

        translations = []
        for input_text in inputs:
            translated_text, _ = self.translator.predict(input_text,
                                            task_str="t2tt",
                                            tgt_lang=LANGUAGE_MAP[target_lang],
                                            src_lang=LANGUAGE_MAP[source_lang]
                                        )
            translations.append(translated_text[0].__str__())
            
        return translations

if __name__ == "__main__":
    m4t_model = My_NMT_T2TT()
    print (m4t_model.translate(["យ៉ាង ណា ក៏ ដោយ បូតុលូសស៊ី ស៊ុត ចូល លើក ទី ៤ នៃ ការ ទាត់ បាល់ ពិន័យ នៃ ប្រកួត នេះ ហើយ បន្ទាប់ មក ម័ររូ ប៊ីហ្គាម៉ាស្កូ និង អេនត្រា ម៉ាស៊ី បាន ស៊ុត ចូល នាំ អោយ អ៊ីតាលី ឈ្នះ ។"]))