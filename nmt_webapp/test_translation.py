import json
import torch
import nemo.collections.nlp as nemo_nlp
from nemo.utils import logging
from utils import split_long_text
from nmt_service import free_cache

model = nemo_nlp.models.machine_translation.\
            MTEncDecModel.from_pretrained(model_name="nmt_zh_en_transformer24x6")

if torch.cuda.is_available():
    model = model.cuda()

max_length = 64 

# load test data 
data = json.load(open('tests/t5_zh_test.json'))

outfile = open(f'tests/t5_zh_output_{max_length}.json', 'w', encoding='utf-8')

for src in data:
    paragraphs, ext_characters = split_long_text(src, max_length=max_length, period_char="。")

    # print ('>>> paragraphs splitted: ', paragraphs)

    # same interface for both nemo and seamless models
    # due to missing translation with batch translation 
    # we translate single paragraph at a time and combine them
    translated_paragraphs = []
    for p in paragraphs:
        translated_paragraphs.extend(model.translate([p],
                                source_lang='zh', 
                                target_lang='en'
                                ))

    # print ('>>> paragraphs translated: ', translated_paragraphs)

    translated_text = ""
    for text, ext_chr in zip(translated_paragraphs, ext_characters):                
        translated_text += (text + ext_chr)
    # strip last space character
    translated_text = translated_text.strip()

    outfile.write(translated_text + "\n\n")

outfile.close()

# try to free cache if necessary
free_cache()