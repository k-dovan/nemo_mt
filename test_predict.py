# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
import torch
import random
import csv
import numpy as np
from seamless_communication.models.inference import Translator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s -- %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


if torch.cuda.is_available():
    device = torch.device("cuda:0")
    dtype = torch.float16
    logger.info(f"Running inference on the GPU in {dtype}.")
else:
    device = torch.device("cpu")
    dtype = torch.float32
    logger.info(f"Running inference on the CPU in {dtype}.")
translator = Translator("seamlessM4T_medium", "vocoder_36langs", device, dtype)



test_src_file = "data/train.merged_data.km"
test_tgt_file = "data/train.merged_data.en"

with open(test_src_file, "r", encoding="utf-8") as src_file:
    src_sentences = src_file.readlines()
with open(test_tgt_file, "r", encoding="utf-8") as tgt_file:
    tgt_sentences = tgt_file.readlines()

assert len(src_sentences) == len(tgt_sentences)

all_indices = set(range(len(src_sentences)))
picked_indices = set(random.choices(list(all_indices), k=100))

np_src_samples = np.array(src_sentences)
np_tgt_samples = np.array(tgt_sentences)

picked_src_samples = [sent.strip('\n') for sent in list(np_src_samples[list(picked_indices)])]
picked_tgt_samples = [sent.strip('\n') for sent in list(np_tgt_samples[list(picked_indices)])]
# Translate a sentence or list of sentences
translations = [ str(translator.predict(
    input_text,
    "t2tt",
    "eng",
    src_lang="khm",
    ngram_filtering=False,
)[0]) for input_text in picked_src_samples]

print (f"source sentences: {picked_src_samples}")
print (f"translated sentences: {translations}")
print (f"target sentences: {picked_tgt_samples}")

rows = zip(picked_src_samples, translations, picked_tgt_samples)

with open("testing_results.csv", "w") as f:
    writer = csv.writer(f)
    # write header
    writer.writerow(["source_sentence", "translated_sentence", "target_sentence"])
    for row in rows:
        # if len(row[0]) > 15:
        writer.writerow(row)




