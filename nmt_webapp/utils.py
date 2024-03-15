import re
from typing import List

def merge_para_chunks(chunks: List[str], max_length: int = 512):
    paragraphs, new_paragraphs = [], []
    paragraph = ""
    acc_length = 0
    for p in chunks:
        if acc_length > 0:
            if acc_length + len(p) < max_length:
                paragraph += p
                acc_length += len(p)
            elif acc_length + len(p) == max_length:
                paragraphs.append(paragraph + p)
                new_paragraphs.append(False)
                paragraph = ""
                acc_length = 0
            elif acc_length + len(p) > max_length:
                paragraphs.append(paragraph)
                new_paragraphs.append(False)
                paragraph = ""
                acc_length = 0
                if len(p) >= max_length:
                    paragraphs.append(p)
                    new_paragraphs.append(False)
                else:
                    paragraph = p
                    acc_length = len(p)
        else:
            if len(p) >= max_length:
                paragraphs.append(p)
                new_paragraphs.append(False)
            else:
                paragraph = p
                acc_length = len(p)
    if acc_length > 0:
        paragraphs.append(paragraph)
        new_paragraphs.append(True)
    # set new paragraph flag to the last element
    new_paragraphs[-1] = True

    return paragraphs, new_paragraphs

def split_long_text(long_text: str, max_length: int = 512, period_char: str = '.'):

    passages = [p for p in re.split(r'\n+', long_text) if len(p.strip()) > 0]
    new_line_characters = re.findall(r'\n+', long_text)

    # split further any passage longer than `max_length`
    paragraphs, new_paragraphs = [], []
    for p in passages:
        if len(p) <= max_length:
            paragraphs.append(p)
            new_paragraphs.append(True)
        else:
            sub_passages = [p for p in p.split(period_char) if len(p.strip()) > 0]
            chunks = []
            for sp in sub_passages:
                if len(sp) < max_length:
                    chunks.append(''.join([sp,period_char]))
                else:
                    steps = len(sp)//max_length
                    if len(sp)%max_length == 0:
                        steps += 1
                    for idx in range(steps-1):
                        chunks.append(sp[idx*max_length:(idx+1)*max_length])
                    chunks.append(sp[(steps-1)*max_length:])
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

if __name__ == "__main__":
    s = "一年多前，有份刊物嘱我写稿，题目已经指定了出来：“如果你只有三个月的寿命，你将会去做些什么事？”我想了很久，一直没有去答这份考卷。  荷西听说了这件事情，也曾好奇的问过我——“你会去做些什么呢？”  当时，我正在厨房揉面，我举起了沾满白粉的手，轻轻的摸了摸他的头发，慢慢的说：“傻子，我不会死的，因为还得给你做饺子呢！”  讲完这句话，荷西的眼睛突然朦胧起来，他的手臂从我身后绕上来抱着我，直到饺子上桌了才放开。  “你神经啦？”我笑问他，他眼睛又突然一红，也笑了笑，这才一声不响的在我的对面坐下来。  以后我又想到过这份欠稿，我的答案仍是那么的简单而固执：“我要守住我的家，护住我丈夫，一个有责任的人，是没有死亡的权利的。”  虽然预知死期是我喜欢的一种生命结束的方式，可是我仍然拒绝死亡。在这世上有三个与我个人死亡牢牢相连的生命，那便是父亲、母亲，还有荷西，如果他们其中的任何一个在世上还活着一日，我便不可以死，连神也不能将我拿去，因为我不肯，而神也明白。  前一阵在深夜里与父母谈话，我突然说：“如果选择了自己结束生命的这条路，你们也要想得明白，因为在我，那将是一个更幸福的归宿。”  母亲听了这话，眼泪迸了出来，她不敢说一句刺激我的话，只是一遍又一遍喃喃的说：“你再试试，再试试活下去，不是不给你选择，可是请求你再试一次。”\n  父亲便不同了，他坐在黯淡的灯光下，语气几乎已经失去了控制，他说：“你讲这样无情的话，便是叫爸爸生活在地狱里，因为你今天既然已经说了出来，使我，这个做父亲的人，日日要活在恐惧里，不晓得那一天，我会突然失去我的女儿。如果你敢做出这样毁灭自己的生命的事情，那么你便是我的仇人，我不但今生要与你为仇，我世世代代都要与你为仇，因为是——你，杀死了我最最心爱的女儿——。”  这时，我的泪水瀑布也似的流了出来，我坐在床上，不能回答父亲一个字，房间里一片死寂，然后父亲站了起来慢慢的走出去。母亲的脸，在我的泪光中看过去，好似静静的在抽筋。  苍天在上，我必是疯狂了才会对父母说出那样的话来。  我又一次明白了，我的生命在爱我的人心中是那么的重要，我的念头，使得经过了那么多沧桑和人生的父母几乎崩溃，在女儿的面前，他们是不肯设防的让我一次又一次的刺伤，而我，好似只有在丈夫的面前才会那个样子。许多个夜晚，许多次午夜梦回的时候，我躲在黑暗里，思念荷西几成疯狂，相思，像虫一样的慢慢啃着我的身体，直到我成为一个空空茫茫的大洞。夜是那样的长，那么的黑，窗外的雨，是我心里的泪，永远没有滴完的一天。我总是在想荷西，总是又在心头里自言自语：“感谢上天，今日活着的是我，痛着的也是我，如果叫荷西来忍受这一分又一分钟的长夜，那我是万万不肯的。幸好这些都没有轮到他，要是他像我这样的活下去，那么我拚了命也要跟上帝争了回来换他。”  失去荷西我尚且如此，如果今天是我先走了一步，那么我的父亲、母亲及荷西又会是什么情况？我从来没有怀疑过他们对我的爱，让我的父母在辛劳了半生之后，付出了他们全部之后，再叫他们失去爱女，那么他们的慰藉和幸福也将完全丧失了，这样尖锐的打击不可以由他们来承受，那是太残酷也太不公平了。\n\n  要荷西半途折翼，强迫他失去相依为命的爱妻，即使他日后活了下去，在他的心灵上会有怎么样的伤痕，会有什么样的烙印？如果因为我的消失而使得荷西的余生再也不有一丝笑容，那么我便更是不能死。  这些，又一些，因为我的死亡将带给我父母及丈夫的大痛苦，大劫难，每想起来，便是不忍，不忍，不忍又不忍。毕竟，先走的是比较幸福的，留下来的，也并不是强者，可是，在这彻心的苦，切肤的疼痛里，我仍是要说——“为了爱的缘故，这永别的苦杯，还是让我来喝下吧！”  我愿意在父亲、母亲、丈夫的生命圆环里做最后离世的一个，如果我先去了，而将这份我已尝过的苦杯留给世上的父母，那么我是死不瞑目的，因为我明白了爱，而我的爱有多深，我的牵挂和不舍便有多长。\n  所以，我是没有选择的做了暂时的不死鸟，虽然我的翅膀断了，我的羽毛脱了，我已没有另一半可以比翼，可是那颗碎成片片的心，仍是父母的珍宝，再痛，再伤，只有他们不肯我死去，我便也不再有放弃他们的念头。  总有那么一天，在超越我们时空的地方，会有六张手臂，温柔平和的将我迎入永恒，那时候，我会又哭又笑的喊着他们——爸爸、妈妈、荷西，然后没有回顾的狂奔过去。  这份文字原来是为另一个题目而写的，可是我拒绝了只有三个月寿命的假想，生的艰难，心的空虚，死别时的碎心又碎心，都由我一个人来承当吧！  父亲、母亲、荷西，我爱你们胜于自己的生命，请求上苍看见我的诚心，给我在世上的时日长久，护住我父母的幸福和年岁，那么我，在这份责任之下，便不再轻言消失和死亡了。  荷西，你答应过的，你要在那边等我，有你这一句承诺，我便还有一个盼望了。"
    
    print (split_long_text(s, max_length=512, period_char='。'))