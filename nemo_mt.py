from nemo.collections.nlp.models import MTEncDecModel

# To get the list of pre-trained models
MTEncDecModel.list_available_models()

# Download and load the a pre-trained to translate from English to Spanish
model = MTEncDecModel.from_pretrained("nmt_zh_en_transformer6x6")
#model = MTEncDecModel.restore_from("nemo_model_v1.ckpt")

# Translate a sentence or list of sentences
translations = model.translate(["这是我年轻时候住的房子。"], source_lang="zh", target_lang="en")

print (translations)
