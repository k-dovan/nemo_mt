import json
from nmt_service import translate

# init params
merge_en_chunks = True, 
replace_doi_terms = True,
translate_by_sentence = True, 
max_length = 64

merge_en = ""
if merge_en_chunks:
    merge_en = "_mergeEN"
else:
    merge_en = "_NOTmergeEN"

doi_term = ""
if replace_doi_terms:
    doi_term = "_DOIterms"
else:
    doi_term = "_NOTDOIterms"

by_sentence = ""
if translate_by_sentence:
    by_sentence = "_BYsentence"
else:
    by_sentence = f"_BYchunk{max_length}"

outfile_name = f"tests/t5_zh_output{merge_en}{doi_term}{by_sentence}.json"

# load test data 
data = json.load(open('tests/t5_zh_test.json'))

outfile = open(outfile_name, 'w', encoding='utf-8')

for src in data:
    
    translated_text = translate(src, langpair="zh-vi")
    
    outfile.write(translated_text + "\n\n")

outfile.close()