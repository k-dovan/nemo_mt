import re
from typing import List
from utils_mapping import read_mapping_zh_en

# ---------------------------- split text based on max_length --------------------------------
def count_quotation_marks(text: str, quote_characters: str):
    count = 0
    for ch in quote_characters:
        count += text.count(ch)
    
    return count

def is_valid_paragraph(text: str, open_quotes: str, close_quotes: str):
    count_open = count_quotation_marks(text, quote_characters=open_quotes)
    count_close = count_quotation_marks(text, quote_characters=close_quotes)
    result = count_open == count_close

    # print ('open count: ', count_open)
    # print ('close count: ', count_close)
    # print ('is valid: ', result)
    return result

def merge_para_chunks(chunks: List[str], 
                      max_length: int = 512, 
                      open_quotes: str =  '“"‘『「',
                      close_quotes: str = '”"’』」'):
    paragraphs, new_paragraphs = [], []
    paragraph = ""
    acc_length = 0
    for p in chunks:
        if acc_length > 0:
            if acc_length + len(p) < max_length:
                paragraph += p
                acc_length += len(p)
            elif acc_length + len(p) == max_length:
                if is_valid_paragraph(paragraph+p, open_quotes, close_quotes):
                    paragraphs.append(paragraph+p)
                    new_paragraphs.append(False)
                    # print ('+01')
                    paragraph = ""
                    acc_length = 0
                else:
                    paragraph += p
                    acc_length += len(p)
            elif acc_length + len(p) > max_length:
                if is_valid_paragraph(paragraph, open_quotes, close_quotes):
                    paragraphs.append(paragraph)
                    new_paragraphs.append(False)
                    # print ('+01')
                    paragraph = ""
                    acc_length = 0
                    if len(p) >= max_length:
                        if is_valid_paragraph(p, open_quotes, close_quotes):
                            paragraphs.append(p)
                            new_paragraphs.append(False)
                            # print ('+01')
                        else:
                            paragraph = p
                            acc_length = len(p)
                    else:
                        paragraph = p
                        acc_length = len(p)
                else:
                    paragraph += p
                    acc_length += len(p)
        else:
            if len(p) >= max_length:
                if is_valid_paragraph(p, open_quotes, close_quotes):
                    paragraphs.append(p)
                    new_paragraphs.append(False)
                    # print ('+01')
                else:
                    paragraph = p
                    acc_length = len(p)
            else:
                paragraph = p
                acc_length = len(p)
    if acc_length > 0:
        # just to make sure the last paragraph valid
        is_valid_paragraph(paragraph, open_quotes, close_quotes)

        paragraphs.append(paragraph)
        new_paragraphs.append(True)
        # print ('+01')
    # set new paragraph flag to the last element
    new_paragraphs[-1] = True

    return paragraphs, new_paragraphs

def split_long_text(long_text: str, 
                    max_length: int = 512, 
                    period_char: str = '。'):

    passages = [p for p in re.split(r'\n+', long_text)]
    new_line_characters = re.findall(r'\n+', long_text)

    # split further any passage longer than `max_length`
    paragraphs, new_paragraphs = [], []
    for p in passages:
        if len(p) <= max_length:
            paragraphs.append(p)
            new_paragraphs.append(True)
        else:
            sub_passages = [p for p in p.split(period_char)]
            chunks = []
            for sp in sub_passages:
                # chunks.append(''.join([sp, period_char]))
                chunks.append(sp)
                
            ext_paragraphs, ext_new_paragraphs = merge_para_chunks(chunks, max_length= max_length)
            paragraphs.extend(ext_paragraphs)
            new_paragraphs.extend(ext_new_paragraphs) 
    # set new paragraph flag to the last element
    new_paragraphs[-1] = False

    # match new-line characters for each paragraph
    ext_characters = []
    i = 0
    for new in new_paragraphs:
        if new:
            ext_characters.append(new_line_characters[i])
            i += 1
        else:
            ext_characters.append(" ")

    return paragraphs, ext_characters


# ---------------------------- split text by sentence ----------------------------------------
def get_valid_quotation_characters(text: str, open_quotes: str, close_quotes: str):
    assert len(open_quotes) == len(close_quotes), "number of open and close quote characters must be equal!"
    
    valid_open_quotes, valid_close_quotes = [], []

    for idx in range(len(open_quotes)):
        q_open = open_quotes[idx]
        q_close = close_quotes[idx]
        count_open = count_quotation_marks(text, [q_open])
        count_close = count_quotation_marks(text, [q_close])
        if count_open == count_close:
            valid_open_quotes.append(q_open)
            valid_close_quotes.append(q_close)
    return valid_open_quotes + valid_close_quotes

def split_long_text_by_sentence_and_quotation(
        long_text: str, 
        period_char: str = '。', 
        comma_char: str = '，',
        open_quotes: str =  '“‘『「',
        close_quotes: str = '”’』」'
        ):
    
    # for replacement
    period_en: str = '.'
    comma_en: str = ','
    quote_en: str = '"'

    # get valid quotation marks
    valid_quotation_characters = get_valid_quotation_characters(long_text, open_quotes, close_quotes)
    valid_splitors = valid_quotation_characters + [period_char, comma_char]

    # build splitor regex
    regx_splitor = f"(?:\\n+)|" + f"(?:[{re.escape(''.join(valid_splitors))}])"

    # print (regx_splitor)
    
    # split long text to span of texts
    passages = [p for p in re.split(regx_splitor, long_text)]
    ext_characters = re.findall(regx_splitor, long_text)

    # convert all punctuations and quotations to english characters
    for idx,_ in enumerate(ext_characters):
        if ext_characters[idx] == period_char:
            if idx == len(ext_characters) - 1:
                ext_characters[idx] = period_en
            elif ext_characters[idx+1] in close_quotes:
                ext_characters[idx] = period_en
            else:
                ext_characters[idx] = period_en + " "
        elif ext_characters[idx] == comma_char:
            if idx == len(ext_characters) - 1:
                ext_characters[idx] = comma_en
            elif ext_characters[idx+1] in close_quotes:
                ext_characters[idx] = comma_en
            else:
                ext_characters[idx] = comma_en + " "
        elif ext_characters[idx] in open_quotes:
            ext_characters[idx] = " " + quote_en
        elif ext_characters[idx] in close_quotes:
            ext_characters[idx] = quote_en + " "
    
    ext_characters += ['']

    print (passages, ext_characters)
    print (len(passages), len(ext_characters))

    return passages, ext_characters

def replace_doi_terms(text: str, lang: str="zh"):
    """
    Fast replace domain of interest terms from chinese to english
    """
    if lang == "zh":
        dict_terms = read_mapping_zh_en()

        for k,v in dict_terms.items():
            text = text.replace(k,v)

        return text
    else:
        return text

def remove_troll_characters(text: str):
    troll_characters = ["\u200b"]
    for tc in troll_characters:
        text = text.replace(tc, "")
    return text

if __name__ == "__main__":
    
    # -------------- Chinese tests --------------------------------------------------------
    # period_char = "。"
    # comma_char = "，"
    # open_quotes = '“‘『「'
    # close_quotes = '”’』」'

    # s = "一年多前，有份刊物嘱我写稿，题目已经指定了出来：“如果你只有三个月的寿命，你将会去做些什么事？”我想了很久，一直没有去答这份考卷。  荷西听说了这件事情，也曾好奇的问过我——“你会去做些什么呢？”  当时，我正在厨房揉面，我举起了沾满白粉的手，轻轻的摸了摸他的头发，慢慢的说：“傻子，我不会死的，因为还得给你做饺子呢！”  讲完这句话，荷西的眼睛突然朦胧起来，他的手臂从我身后绕上来抱着我，直到饺子上桌了才放开。  “你神经啦？”我笑问他，他眼睛又突然一红，也笑了笑，这才一声不响的在我的对面坐下来。  以后我又想到过这份欠稿，我的答案仍是那么的简单而固执：“我要守住我的家，护住我丈夫，一个有责任的人，是没有死亡的权利的。”  虽然预知死期是我喜欢的一种生命结束的方式，可是我仍然拒绝死亡。在这世上有三个与我个人死亡牢牢相连的生命，那便是父亲、母亲，还有荷西，如果他们其中的任何一个在世上还活着一日，我便不可以死，连神也不能将我拿去，因为我不肯，而神也明白。  前一阵在深夜里与父母谈话，我突然说：“如果选择了自己结束生命的这条路，你们也要想得明白，因为在我，那将是一个更幸福的归宿。”  母亲听了这话，眼泪迸了出来，她不敢说一句刺激我的话，只是一遍又一遍喃喃的说：“你再试试，再试试活下去，不是不给你选择，可是请求你再试一次。”\n  父亲便不同了，他坐在黯淡的灯光下，语气几乎已经失去了控制，他说：“你讲这样无情的话，便是叫爸爸生活在地狱里，因为你今天既然已经说了出来，使我，这个做父亲的人，日日要活在恐惧里，不晓得那一天，我会突然失去我的女儿。如果你敢做出这样毁灭自己的生命的事情，那么你便是我的仇人，我不但今生要与你为仇，我世世代代都要与你为仇，因为是——你，杀死了我最最心爱的女儿——。”  这时，我的泪水瀑布也似的流了出来，我坐在床上，不能回答父亲一个字，房间里一片死寂，然后父亲站了起来慢慢的走出去。母亲的脸，在我的泪光中看过去，好似静静的在抽筋。  苍天在上，我必是疯狂了才会对父母说出那样的话来。  我又一次明白了，我的生命在爱我的人心中是那么的重要，我的念头，使得经过了那么多沧桑和人生的父母几乎崩溃，在女儿的面前，他们是不肯设防的让我一次又一次的刺伤，而我，好似只有在丈夫的面前才会那个样子。许多个夜晚，许多次午夜梦回的时候，我躲在黑暗里，思念荷西几成疯狂，相思，像虫一样的慢慢啃着我的身体，直到我成为一个空空茫茫的大洞。夜是那样的长，那么的黑，窗外的雨，是我心里的泪，永远没有滴完的一天。我总是在想荷西，总是又在心头里自言自语：“感谢上天，今日活着的是我，痛着的也是我，如果叫荷西来忍受这一分又一分钟的长夜，那我是万万不肯的。幸好这些都没有轮到他，要是他像我这样的活下去，那么我拚了命也要跟上帝争了回来换他。”  失去荷西我尚且如此，如果今天是我先走了一步，那么我的父亲、母亲及荷西又会是什么情况？我从来没有怀疑过他们对我的爱，让我的父母在辛劳了半生之后，付出了他们全部之后，再叫他们失去爱女，那么他们的慰藉和幸福也将完全丧失了，这样尖锐的打击不可以由他们来承受，那是太残酷也太不公平了。\n\n  要荷西半途折翼，强迫他失去相依为命的爱妻，即使他日后活了下去，在他的心灵上会有怎么样的伤痕，会有什么样的烙印？如果因为我的消失而使得荷西的余生再也不有一丝笑容，那么我便更是不能死。  这些，又一些，因为我的死亡将带给我父母及丈夫的大痛苦，大劫难，每想起来，便是不忍，不忍，不忍又不忍。毕竟，先走的是比较幸福的，留下来的，也并不是强者，可是，在这彻心的苦，切肤的疼痛里，我仍是要说——“为了爱的缘故，这永别的苦杯，还是让我来喝下吧！”  我愿意在父亲、母亲、丈夫的生命圆环里做最后离世的一个，如果我先去了，而将这份我已尝过的苦杯留给世上的父母，那么我是死不瞑目的，因为我明白了爱，而我的爱有多深，我的牵挂和不舍便有多长。\n  所以，我是没有选择的做了暂时的不死鸟，虽然我的翅膀断了，我的羽毛脱了，我已没有另一半可以比翼，可是那颗碎成片片的心，仍是父母的珍宝，再痛，再伤，只有他们不肯我死去，我便也不再有放弃他们的念头。  总有那么一天，在超越我们时空的地方，会有六张手臂，温柔平和的将我迎入永恒，那时候，我会又哭又笑的喊着他们——爸爸、妈妈、荷西，然后没有回顾的狂奔过去。  这份文字原来是为另一个题目而写的，可是我拒绝了只有三个月寿命的假想，生的艰难，心的空虚，死别时的碎心又碎心，都由我一个人来承当吧！  父亲、母亲、荷西，我爱你们胜于自己的生命，请求上苍看见我的诚心，给我在世上的时日长久，护住我父母的幸福和年岁，那么我，在这份责任之下，便不再轻言消失和死亡了。  荷西，你答应过的，你要在那边等我，有你这一句承诺，我便还有一个盼望了。"
    # s = "商务部22日发布的数据显示，8月份，各级商务主管部门深入组织开展“消费提振年”系列促消费活动，着力提振汽车、家居等大宗消费，促进服务消费，发展新型消费，推动消费持续恢复和扩大，发挥消费拉动经济增长的基础性作用。当月社会消费品零售总额3.79万亿元，同比增长4.6%，增速比上月加快2.1个百分点；1至8月累计30.23万亿元，同比增长7.0%。\n据商务部消费促进司负责人介绍，当前消费市场主要呈现以下几方面特点：\n商品销售稳步回升。升级类商品消费需求持续释放，绿色智能产品受到欢迎。8月份，商品零售额同比增长3.7%，增速比上月加快2.7个百分点。从商品类别看，近七成商品类值零售额同比增速较上月加快。其中，限额以上单位化妆品、通讯器材、金银珠宝、家具同比分别增长9.7%、8.5%、7.2%和4.8%。新能源汽车销售旺盛，8月份销量同比增长27%，1至8月同比增长39.2%，占新车销量比重达29.5%。\n服务消费较快增长。暑期居民出游热度较高，带动餐饮、住宿、旅游、交通等服务消费较快增长。8月份，全国餐饮收入4212亿元，同比增长12.4%；暑运期间，全国铁路、民航旅客运输量分别达8.3亿和1.3亿人次，均创历史同期新高；暑期档电影票房收入超206亿元，同比增长约1.26倍，为历史同期最高纪录。1至8月，服务零售额同比增长19.4%。\n新型消费快速发展。网络零售保持较快增长，1至8月全国网上零售额9.54万亿元，同比增长12.1%，其中实物商品网上零售额7.98万亿元，增长9.5%，占社会消费品零售总额比重达26.4%。8月份，全国快递业务量同比增长15%左右，业务收入增长约9%。\n农村消费加快恢复。8月份，乡村消费品零售额4959亿元，同比增长6.3%，增速比上月加快2.5个百分点，比城镇消费品零售额增速快1.9个百分点。1至8月，乡村消费品零售额3.99万亿元，同比增长7.6%，增速比城镇消费品零售额快0.7个百分点。\n商务部新闻发言人何亚东说，消费一头连着宏观经济大盘，一头连着千家万户美好生活。中秋、国庆“双节”是传统的消费旺季，商务部正在组织开展“金九银十”系列促消费活动，更好满足居民节日消费需求，推动消费持续恢复和扩大。“我们将聚焦重点，多措并举，发挥好消费的基础性作用，为推动经济持续恢复向好贡献力量。”何亚东说。"
    # s= "金秋时节，硕果累累。在这个收获的季节里，中国迎来特殊的节日——第六届中国农民丰收节。2018年，经党中央批准、国务院批复，每年农历秋分被设立为“中国农民丰收节”。这是中国第一个在国家层面专门为农民设立的重大法定节日，充分体现了党中央对“三农”工作的高度关注、对农民群众的深切关爱、对国家粮食安全的高度重视。\n中国农民丰收节是亿万农民庆祝丰收、享受丰收的节日，在新时代具有重大的现实意义，进一步体现了党和国家及社会各界对农民群众的尊重和关爱，彰显了农业对国民经济和社会发展的关键性基础地位和价值，传承和弘扬了中华农耕文明和伟大民族精神，持续推动乡村振兴、农业农村现代化不断打开新局面、取得新成效、迈上新台阶。\n庆祝农民丰收节，极大调动了农民等社会各界的主动性、积极性和创造性，广泛凝聚全社会推动“三农”事业高质量发展、团结奋斗维护国家粮食安全，加快建设农业强国的信心和合力。近年来，中国粮食生产稳步发展，粮食等重要农产品供给总量、结构、质量持续优化，市场供应充足、运行总体平稳，防范化解重大风险挑战能力不断增强，粮食安全保障水平显著提升，切实端稳端牢了中国饭碗。\n“藏粮于地、藏粮于技”战略深入实施，耕地和种子两个要害越抓越牢固，中国粮食综合生产能力不断提高，为农民丰收奠定了坚实基础。国家实施最严耕地保护制度，大力推进高标准农田建设和国家黑土地保护工程，划定粮食生产功能区和重要农产品生产保护区，推进节约集约用地，挖掘后备耕地增产潜力，加快实施大中型灌区续建配套与现代化改造和新建大型灌区，提升水旱灾害防御能力，全国耕地总量持续下降态势得到初步遏制，2021年和2022年连续两年实现净增加。\n2022年底，全国累计建成10亿亩高标准农田，耕地灌溉面积超过10亿亩，耕地质量和防灾减灾能力不断提升，为农民从事农业生产和实现丰产丰收提供更加优质、更加广阔、更有保障的耕地空间。\n同时，国家深入实施种业振兴行动，组织开展国家育种联合攻关，基本实现粮食作物良种全覆盖，加强化肥产、供、储、销调控体系建设，保障农业生产用肥、用药安全，加强农作物病虫害防治能力建设，推广绿色防控等技术，促进增产增效，农业科技进步贡献率、主要农作物良种覆盖率、农作物耕、种、收综合机械化率分别从2017年的52.5%、95%、67.2%提升到2022年的62.4%、96%、73%。这为农民丰收夯实了种源基础、插上了科技的翅膀。\n此外，中国农业保护支持政策制度体系不断健全、持续优化，财政金融不断加大对“三农”的倾斜支持力度，为农民丰收夯实了政策保障、财政支持，更强化了金融服务，使农民在丰收的道路上享受更多政策红利、财政补贴和金融支持。\n在党中央坚强领导和各地区各部门共同努力下，全国实现了大丰收，粮食产量连续8年稳定在1.3万亿斤以上，2022年粮食产量13731亿斤，粮食单产每亩386.8公斤，较5年前分别提升了498亿斤、13公斤，人均粮食占有量达486.1公斤，高于国际公认的400公斤的粮食安全线。中国以占世界百分之九的耕地、百分之六的淡水资源，养育了世界近五分之一的人口，从当年四亿人吃不饱到今天十四亿多人吃得好，有力回答了“谁来养活中国”的问题。\n今年是全面贯彻党的二十大精神开局之年，也是加快建设农业强国的起步之年。这使今年的中国农民丰收节更具有里程碑意义。当前，全国各地秉承“庆祝丰收、弘扬文化、振兴乡村”的原则，正举办丰富多彩的群众庆祝丰收节庆活动，展现“三农”发展成就，展示农业农村现代化美好前景，弘扬传承中华优秀传统文化，丰富发展中华农耕文明。这必将进一步营造全社会关注农业、关心农村、关爱农民的浓厚氛围，激发广大农民群众创造美好生活的干劲，为全力确保粮食和重要农产品稳定安全供给、全面推进乡村振兴、加快建设农业强国注入强大动力。"
    # s = "AIS信号显示，2月20日，尼米兹号航母打击群成员“迪云”号与“韦恩·迈耶”号驱逐舰经苏里高海峡进入菲律宾海。2月19日，打击群成员“迪卡特”号与“韦恩·迈耶”号驱逐舰在苏禄海活动，同日，一架美海军P-8A反潜巡逻机自菲律宾克拉克机场起飞，提供ISR（情报、侦察、监视）支援。据三艘驱逐舰航行轨迹推断，尼米兹号航母打击群已于2月18日自巴拉巴克海峡进入苏禄海，结束此次南海部署。\n尼米兹号航母打击群此次部署活动时间长，轨迹呈闭环。打击群于1月12日自巴士海峡进入南海，活动时间长达38天，是近年来美海军航母在南海部署时间最长的一次。部署期间，除短暂访问新加坡和配合美防长访菲外，长时间位印马交界水域和万安盆地以南海域活动。2月11日开始，尼米兹号航母打击群还与马金岛号两栖戒备群在此进行了“联合远征打击力量（ESF）”作战训练"
    # paras = split_long_text(s, max_length=256)
    # print ('number of paragraphs: ', len(paras[1]))
    # for idx, para in enumerate(paras[0]):
    #     print (idx, para)

    # split_long_text_by_sentence_and_quotation(s,period_char=period_char, comma_char=comma_char,
    #                                           open_quotes=open_quotes, close_quotes=close_quotes)

    # -------------- Campuchia tests --------------------------------------------------------
    period_char = "។"
    comma_char = ","
    open_quotes =  '«“'
    close_quotes = '»”'

    # s = "ដោយមាន​ឪពុក​ម្តាយ​ជា​កសិករ​ក្រីក្រ​ ​កុមារី​ ​រក្សា​ ​ជា​កូនពៅ​ក្នុងចំណោម​បងប្អូនបង្កើត​ទាំង​ប្រាំ​នាក់​ក្នុង​គ្រួសារ​បាន​និយាយ​ថា​ ​កង់​នេះ​គឺ​ជាអំណោយ​ដ៏​ធំ​ដំបូង​ក្នុង​ជីវិត​របស់​ខ្លួន​ ​ហើយ​សន្យា​ថា​នឹង​ថែរក្សា​កង់​នេះ​អោយ​បាន​ល្អ​។​\n\n​បន្ទាប់ពី​ទទួល​បាន​កង់​ ​រក្សា​បាន​មើល​កង់​ថ្មី​របស់​ខ្លួន​ដោយ​ស្នាម​ញញឹម​ ​ហើយ​ស្ទាប​ដៃចង្កូត​ រួ​ចចុច​កណ្តឹង​ ​មុន​ពេល​ជិះ​ចុះ​ជិះ​ឡើង​នៅ​ក្នុង​បរិវេណ​សាលា​។​\n\n​ផ្ទះ​របស់​រក្សា​មាន​ចម្ងាយ​ប្រហែល​ ​៥​គីឡូម៉ែត្រ​ពី​សាលារៀន​ដោយ​នាង​បាន​និយាយ​ថា​ខ្លួន​នឹង​លែង​ជិះកង់​ចាស់​ទៀតហើយ​ដោយសារតែ​វា​ពិបាក​ជិះ​ពេក​។​\n\n​រក្សា​បាន​ប្រាប់​ X​in​h​u​a​ ​ថា​ “​កង់​ចាស់​របស់​ខ្ញុំ​គឺ​តូច​។​ ​នៅ​ពេល​ធ្លាក់​ច្រ​វ៉ា​ក់ ​គឺ​ពិបាក​ដាក់​វា​ឡើងវិញ​ ​ហើយ​ពេលខ្លះ​បែកកង់​នៅពេលដែល​ក្នុង​ជិះ​វា​”​។​\n\n​រក្សា​បាន​បន្ថែម​ថា​ ​ពេលខ្លះ​នាង​ត្រូវ​ដើរទៅ​សាលារៀន​ ​ហើយ​ទៅដល់​សាលា​យឺត​ដោយសារ​កង់​របស់​ខ្លួន​ខូច​។​\n\n​រក្សា​បាន​បន្ថែម​ថា​ “​ខ្ញុំ​សប្បាយរីករាយ​នៅ​ពេល​ទទួល​បាន​កង់​ថ្មី​នេះ​ ​ដូច្នេះ​ខ្ញុំ​នឹង​អាច​ទៅ​សាលារៀន​ទាន់ពេល​។​ ​កង់​នេះ​គឺ​ស្អាត​ ​ហើយ​ខ្ញុំ​ចូលចិត្ត​វា​”​។​ “​ខ្ញុំ​នឹង​ខំប្រឹង​រៀន​ដើម្បី​បាន​ពិន្ទុ​ល្អ​ ​ហើយ​ខ្ញុំ​ចង់​ធ្វើជា​គ្រូបង្រៀន​ពេល​ធំឡើង​”​។​"

    s = "​អ្នកចូលរួម​ប្រមាណ​ ​៣​២​០​ ​នាក់​ ​រួម​ទាំង​អ្នកបង្កើត​គោល​នយោបាយ​ ​អ្នកសេដ្ឋកិច្ច​ ​អ្នកដឹកនាំ​ធុរកិច្ច​ ​និង​អ្នកដឹកនាំ​ធនាគារ​ ​និង​មីក្រូ​ហិរញ្ញវត្ថុ​ ​បាន​ចូលរួម​ក្នុង​ព្រឹត្តិការណ៍​នេះ​ ​ដើម្បី​ពិភាក្សា​អំពី​និន្នាការ​ចុងក្រោយ​ ​បញ្ហា​ប្រឈម​ ​និង​ដំណោះស្រាយ​ក្នុង​វិ​ស័​យ​នេះ​។​\n\n​នៅ​ក្នុង​សន្និសីទ​នេះ​ ​ភាគី​ពាក់ព័ន្ធ​បាន​លើកឡើង​ពី​កិច្ច​ខិតខំ​ប្រឹងប្រែង​ ​និង​គំនិត​ផ្តួចផ្តើម​ផ្សេងៗ​ ​ដើម្បី​លើក​ក​ម្ពស់ ​និង​ពង្រឹង​បរិ​យា​ប័ន្ន​ហិរញ្ញវត្ថុ​ ​ប្រកបដោយ​ការទទួលខុសត្រូវ​ ​និង​ការ​ការពារ​អតិថិជន​។​\n\n​ការ​ប្តេជ្ញា​ចិត្ត​តាម​វិ​ស័​យ​នេះ​ធ្វើឡើង​ចំ​ពេល​មានការ​ខិតខំ​ប្រឹងប្រែង​យ៉ាង​ទូលំទូលាយ​របស់​រាជរដ្ឋាភិបាល​កម្ពុជា​ក្នុង​ការ​ពង្រឹង​ការ​ការពារ​អ្នកប្រើប្រាស់​។​\n\n​កាលពីដើម​ឆ្នាំនេះ​ ​ក្រសួងមហាផ្ទៃ​ ​និង​ធនាគារជាតិនៃកម្ពុជា​ ​បាន​ចេញ​សេចក្តីថ្លែង​ការណ៍​រួម​មួយ​ ​ដើម្បី​ទប់​ស្កាត់​សកម្មភាព​ក​ម្ចី​ខុសច្បាប់​។​\n\n​លើស​ពី​នេះ​ ​អគ្គនាយកដ្ឋាន​ការពារ​អ្នកប្រើប្រាស់​ ​កិច្ច​ការប្រកួតប្រជែង​និង​បង្ក្រាប​ការ​ក្លែង​បន្លំ​ ​នៃ​ក្រសួង​ពាណិជ្ជកម្ម​ ​បាន​និង​កំពុង​ពង្រឹង​យ៉ាងសកម្ម​នូវ​វិធានការ​ការពារ​អ្នកប្រើប្រាស់​របស់​ខ្លួន​។​\n​A​K​P​-​ជា​ ​វណ្ណៈ​"
    s = s.replace("\u200b", "")
    split_long_text_by_sentence_and_quotation(s,period_char=period_char, comma_char=comma_char,
                                              open_quotes=open_quotes, close_quotes=close_quotes)

    # -------------- Laos tests --------------------------------------------------------   
    # period_char = "."
    # comma_char = ","
    # open_quotes =  '“'
    # close_quotes = '”'

    # s = "​ຂປລ. ພິທີເຊັນບົດບັນທຶກ ຄວາມເຂົ້າໃຈ ຮ່ວມມືພັດທະນາວຽກງານ ຫັນເປັນທັນສະໄໝ (ຫັນເປັນດີຈິຕອນ) ລະຫວ່າງ ຫ້ອງວ່າການສູນກາງພັກ ແລະ ກະຊວງ ເຕັກໂນໂລຊີ ແລະ ການສື່ສານ ໄດ້ຈັດຂຶ້ນໃນວັນທີ 28 ພະຈິກ 2023 ລະຫວ່າງ ທ່ານ ທອງສະລິດ ມັງໜໍ່ເມກ ຄະນະເລຂາທິການສູນກາງພັກ, ເລຂາຄະນະພັກ, ຫົວໜ້າຫ້ອງວ່າການສູນກາງພັກ ກັບ ທ່ານ ບໍ່ວຽງຄຳ ວົງດາລາ ກຳມະການສູນກາງພັກ, ເລຂາຄະນະພັກ, ລັດຖະມົນຕີ ກະຊວງເຕັກໂນໂລຊີ ແລະ ການສື່ສານ ໂດຍມີພາກສ່ວນກ່ຽວຂ້ອງ ຂອງທັງສອງຝ່າຍ ເຂົ້າຮ່ວມເປັນສັກຂີພິຍານ.\n\n          ການເຊັນສັນຍາຮ່ວມມືກັນ ໃນຄັ້ງນີ້, ເພື່ອເປັນບ່ອນອີງ ໃນການຮ່ວມມືຄົ້ນຄວ້າ,​ ແລກປ່ຽນບົດຮຽນ, ພັດທະນາ, ແລະ ນຳໃຊ້ເຄື່ອງມືດີຈິຕອນ ເພື່ອຫັນວຽກງານ ຫ້ອງວ່າການສູນກາງພັກ ໃຫ້ເປັນທັນສະໄໝ ເທື່ອລະກ້າວ ເຊິ່ງທັງສອງຝ່າຍ ຈະໄດ້ຮ່ວມມືກັນ ໃນການຄົ້ນຄວ້າສ້າງທ່າແຮງ ເພື່ອປັບປຸງ ແລະ ພັດທະນາພື້ນຖານໂຄງລ່າງ ລະບົບເຄືອຂ່າຍ ແລະ ລະບົບສູນຂໍ້ມູນ ເພື່ອເກັບຮັກສາຂໍ້ມູນ ຂອງວຽກງານຫ້ອງວ່າການສູນກາງພັກ; ຮ່ວມມືໃນການພັດທະນາ ແລະ ສົ່ງເສີມການນຳໃຊ້ ລະບົບບໍລິຫານ ລັດດີຈິຕອນ ເຂົ້າໃນວຽກງານ ຂອງຫ້ອງວ່າການສູນກາງພັກ ໃຫ້ມີປະສິດທິພາບ, ຮັບປະກັນຄວາມປອດໄພ ແລະ ມີຄວາມຍືນຍົງ. ພ້ອມທັງ ຮ່ວມມືກັນຄົ້ນຄວ້າ ພັດທະນາລະບົບເຊື່ອມໂຍງຂໍ້ມູນຂ່າວສານ ລະ ຫວ່າງ ຫ້ອງວ່າການສູນກາງພັກ ກັບພາກສ່ວນຕ່າງໆ ແຕ່ຂັ້ນສູນກາງ ຮອດທ້ອງຖິ່ນ, ພັດທະນາ ແລະ ຍົກລະດັບຄວາມຮູ້ ຄວາມສາມາດຂອງ ພະນັກງານ-ລັດຖະກອນ, ແລກປ່ຽນຂໍ້ມູນຂ່າວສານ, ປະສົບການ, ກອງປະຊຸມປຶກສາຫາລື, ສຳມະນາ, ຝຶກອົບຮົມ ແລະ ອື່ນໆ. ພາຍຫລັງການລົງນາມ ບົດບັນທຶກຄວາມເຂົ້າໃຈ (MOU) ສະບັບນີ້ແລ້ວ, ທັງ 2 ຝ່າຍ ຈະໄດ້ພ້ອມກັນຄົ້ນຄ້ວາ ແຕ່ງຕັ້ງຄະນະຮັບຜິດຊອບ ເພື່ອເຮັດວຽກຮ່ວມກັນ ຫັນເປັນດີຈິຕອນ ວຽກງານການບໍລິຫານຫ້ອງການ ແລະ ນຳໃຊ້ເຄື່ອງມືດີຈິຕອນ ເຂົ້າໃນວຽກງານຫ້ອງວ່າການ ແລະ ເຊື່ອມຂໍ້ມູນສູນກາງພັກ ທົ່ວປະເທດ, ຕອບສະໜອງໄດ້ ຕາມແນວທາງນະໂຍບາຍຂອງພັກ, ວິໄສທັດ ຍຸດທະສາດ ແລະ ແຜນພັດທະນາ ເສດຖະກິດດີຈິຕອນ ຂອງ ສປປ ລາວ.\n\n          ປັດຈຸບັນ, ສະພາບການຄຸ້ມຄອງ ແລະ ນຳໃຊ້ລະບົບໄອຊີທີ ຂອງຫ້ອງວ່າການສູນກາງພັກ ເຫັນວ່າຍັງມີຫລາຍດ້ານ ທີ່ຕ້ອງໄດ້ເອົາໃຈໃສ່ຢ່າງຕັ້ງໜ້າ ເປັນຕົ້ນ, ນິຕິກຳລະອຽດ ເພື່ອເປັນບ່ອນອີງ ໃນການຄຸ້ມຄອງ ແລະ ສົ່ງເສີມວຽກການຫັນເປັນທັນສະໄໝ ຍັງບໍ່ຄົບຖ້ວນ, ການປະຕິບັດພາລະບົດບາດ ຄຸ້ມຄອງມະຫາພາກ ກ່ຽວກັບຂໍ້ມູນ ຂ່າວສານຂອງພັກ ຍັງບໍ່ທັນເປັນລະບົບ ແລະ ແຂງແຮງ, ນັກວິຊາການຄຸ້ມຄອງເຕັກນິກ ຍັງຈຳກັດ ທັງດ້ານປະລິມານ ແລະ ຄຸນນະພາບ; ຜູ້ຊົມໃຊ້ເຄື່ອງ ມືໄອຊີທີ ເຫັນໄດ້ບົດບາດ ຄວາມສໍາຄັນ ແລະ ມີຈໍານວນເພີ່ມຂຶ້ນ; ພື້ນຖານໂຄງລ່າງ ວັດຖຸ-ເຕັກນິກ ເປັນຕົ້ນ, ເຄື່ອງອຸປະກອນລະ ບົບເຄືອຂ່າຍອິນເຕີເນັດ ແລະ ເຄື່ອງເຊີເວີ ສ່ວນຫລາຍ ແມ່ນເຄື່ອງເກົ່າ ຕົກສະເປັກ ເຮັດໃຫ້ການນໍາໃຊ້ຕົວຈິງ ບໍ່ສອດຄ່ອງກັບລະບົບໂປລແກຣມໃໝ່; ການນຳໃຊ້ລະບົບບໍລິຫານ ລັດດີຈິຕອນ ເປັນຕົ້ນ ລະບົບກອງປະຊຸມທາງໄກ G-share ໄດ້ມີພື້ນຖານທີ່ດີຈຳນວນໜຶ່ງ, ສ່ວນຫລາຍແມ່ນນໍາໃຊ້ ສື່ສານຜ່ານລະບົບ whatsapp ເຊິ່ງມີຄວາມສ່ຽງ ຕໍ່ຄວາມປອດໄພ ດ້ານຂໍ້ມູນ, ສ່ວນລະບົບອື່ນໆ ແມ່ນນຳໃຊ້ໜ້ອຍ ຫລື ບໍ່ໄດ້ນໍາໃຊ້ເລີຍ.\n\nຂ່າວ: ທະນູທອງ​"
    # s = s.replace("\u200b", "")
 
    # split_long_text_by_sentence_and_quotation(s,period_char=period_char, comma_char=comma_char,
    #                                           open_quotes=open_quotes, close_quotes=close_quotes)