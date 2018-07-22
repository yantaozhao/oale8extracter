# coding=utf-8
# python3.4.3

# update date:2015-12-21

"""
从file_in文件中读取文本，比对file_words_pool文件(同时排除known内容)，若单词存在则统计结果'word\t\tcount'放到file_out中

说明：使用nltk还原单词.
nltk_data的使用，nltk.download()下面几个数据包:
  wordnet
  averaged_perceptron_tagger
  punkt
"""

import os
import os.path
import sys
import re
import nltk
import nltk.stem


# 全局文件
file_all_words_pool = os.getcwd() + os.sep + 'ahd_wordbook_words.txt'  # 单词池
file_known_words_pool = os.getcwd() + os.sep + 'known.txt'  # 排除池
file_in = os.getcwd() + os.sep + 'article.txt'
file_out = os.getcwd() + os.sep + 'word.txt'


def main():
    print('\n usage: script.py [poolfile knownfile infile outfile]\n')
    _r = input('按[R]开始运行，其它任意键退出:')
    if 'r' != _r.strip().lower():
        print('Nothing Done.')
        return

    os.chdir(sys.path[0])
    global file_all_words_pool, file_known_words_pool, file_in, file_out
    v = sys.argv
    if len(v) > 1:
        file_all_words_pool = v[1]
    if len(v) > 2:
        file_known_words_pool = v[2]
    if len(v) > 3:
        # file_in = v[3]
        file_in = os.pardir + os.sep + v[3] if os.path.exists(os.pardir + os.sep + v[3]) else v[3]
    if len(v) > 4:
        # file_out = v[4]
        file_out = os.pardir + os.sep + v[4] if os.path.exists(os.pardir + os.sep + v[3]) else v[4]
    if not ((os.path.exists(file_all_words_pool)) and (os.path.exists(file_in))):
        print('文件不存在,返回')
        return

    _flag_file_exist = os.path.exists(file_known_words_pool)
    try:
        with open(file_all_words_pool, 'r', encoding='utf-8') as fd_pool, \
                open(file_known_words_pool, 'r' if _flag_file_exist else 'w+', encoding='utf-8') as fd_known, \
                open(file_in, 'r', encoding='utf-8') as fd_in, \
                open(file_out, 'w+', encoding='utf-8') as fd_out:

            if fd_pool.closed or fd_known.closed or fd_in.closed or fd_out.closed:
                print('open发生异常,返回')
                return

            # 整理输入
            print('整理读入内容:', end='', flush=True)
            _article = fd_in.read()
            _list_deform_word_ptn = [  # 复数s/es
                                       (r'([^aeiou])ies$', r'\1y'),
                                       (r'(ch|sh|o|x|s)es$', r'\1'),
                                       (r'([a-zA-Z])ves$', r'\1fe'),
                                       (r'([a-zA-Z])s$', r'\1'),
                                       # 现在分词ing
                                       (r'([a-zA-Z])ying$', r'\1ie'),
                                       (r'([^aeiou][aeiou])([^aeiou])\2ing$', r'\1\2'),
                                       (r'([a-zA-Z])ing$', r'\1'),
                                       (r'([a-zA-Z])ing$', r'\1e'),
                                       # 过去分词ed
                                       (r'([^aeiou])ied$', r'\1y'),
                                       (r'([^aeiou][aeiou])([^aeiou])\2ed$', r'\1\2'),
                                       (r'([e])d$', r'\1'),
                                       (r'([a-zA-Z])ed$', r'\1'),
                                       # 副词回形容词
                                       (r'([a-zA-Z])ily$', r'\1y'),
                                       (r'([a-zA-Z])ly$', r'\1'),
                                       (r'([a-zA-Z])bly$', r'\1ble'),
                                       # 形容词回名词
                                       (r'([a-zA-Z])(ful|ous|less|ish|en)$', r'\1'),
                                       (r'([a-zA-Z])ent$', r'\1ence'),
                                       (r'([a-zA-Z])y$', r'\1'),
                                       # 比较级最高级
                                       (r'([aeiou])([^aeiou])(\2)(er|est)$', r'\1\2'),
                                       (r'([^aeiou])(i)(er|est)$', r'\1y'),
                                       (r'([a-zA-Z])(er|est)$', r'\1'),
                                       (r'([a-zA-Z])(er|est)$', r'\1e'),
                                       # 一些常见前缀后缀
                                       (
                                           r'^(anti|auto|bio|centi|con|de|dis|down|en|ex|extra|fore|homo|hyper|infra|inter|kilo|macro|micro|mid|milli|mini|mis|mono|non|out|over|para|per|post|pre|pro|pseudo|re|semi|sub|super|tele|trans|tri|ultra|un|under|uni|up|with)([a-zA-Z])',
                                           r'\2'),
                                       (
                                           r'([a-zA-Z])(able|age|al|an|ance|ancy|ant|ary|ate|ation|ee|ence|ency|ent|er|ern|ery|ese|fold|ful|hood|ian|ible|ical|ice|ify|ion|ious|ise|ish|ism|ist|istic|ition|ity|ive|ize|less|let|like|logy|ment|most|ness|ology|or|ory|ous|ship|some|ster|th|ure|ward|wise)$',
                                           r'\1'),
                                       (r'([a-zA-Z])(age|ant|eer|ent|er|ery|ity|or|ory|ure)$', r'\1e'),
                                       # 名词动词等其他
                                       (r'([a-zA-Z])ation(s?)$', r'\1ate'),
                                       (r'([a-zA-Z])tion(s?)$', r'\1te'),
                                       (r'([a-zA-Z])tion(s?)$', r'\1t'),
                                       (r'([a-zA-Z])ibilit(y|ies)$', r'\1ible'),
                                       (r'([a-zA-Z])ifier(s?)$', r'\1ify'),
                                       (r'([a-zA-Z])age(s?)$', r'\1'),
                                       (r'([a-zA-Z])ance(s?)$', r'\1e'),
                                       (r'([a-zA-Z])ure(s?)$', r'\1'),
                                       (r'([a-zA-Z])(er|eer|or)(s?)$', r'\1'),
                                       (r'([a-zA-Z])ment(s?)$', r'\1')
                                       ]  # 保留供后面单词变形

            _list_sub_ptn = [(r' {0,3}- {0,3}\n {0,3}', r''),  # 换行'-'连字符
                             (r'([a-zA-Z])([0-9]+)', r'\1 '),  # 字母数字
                             (r'([0-9]+)([a-zA-Z])', r' \2'),  # 数字字母
                             (r'([a-z])([0-9]*)([A-Z])', r'\1 \3'),  # 驼峰
                             (r'_', r' ')]  # 下划线
            for _p in _list_sub_ptn:
                _article = words_to_normal_form(_article, ptn=_p[0], new=_p[1])
            print('\t50%', end='', flush=True)

            _list_caps_ptn = [r'(^|\n)( {0,3}[A-Z])',
                              r'( {0,3})(\. {0,3}[A-Z])']  # 行首、句点后首字母转小写
            for _p in _list_caps_ptn:
                _article = words_to_normal_form(_article, ptn=_p)

            _list_in = nltk_get_wordlist(_article)
            # 常见变形的试探
            # _list_in = re.split(r'\W+', _article)
            # _list_in = list(set(_list_in))
            _list_in.sort()  # 未去重复
            try:
                del _list_sub_ptn, _list_caps_ptn
            finally:
                print("\t100%%\n待选:%d" % len(_list_in), flush=True)

            _list_words_pool = fd_pool.read().split('\n')
            _list_known_pool = fd_known.read().split('\n')

            # 生成统计词典
            _dict_counter = {}
            _dict_finder = {'-1': ''}
            for _w in _list_in:
                _fragment = _w = _w.strip()
                if _fragment in _dict_finder:
                    if len(_dict_finder[_fragment].strip()) > 0:
                        _is_in = True
                    else:
                        _is_in = False
                        continue
                else:
                    _dict_finder.clear()
                    _dict_finder[_fragment] = ''
                    _is_in = False

                    _deform_finished = False
                    _deform_order = 0
                    while True:
                        if (_w in _list_known_pool) or (_w.lower() in _list_known_pool):
                            _is_in = False
                            break
                        elif _w.lower() in _list_words_pool:  # 优先选小写
                            _dict_finder[_fragment] = _w.lower()
                            _is_in = True
                            break
                        elif _w in _list_words_pool:
                            _dict_finder[_fragment] = _w
                            _is_in = True
                            break
                        elif not _deform_finished:  # 单词变形
                            while not _deform_finished:
                                try:
                                    _p = _list_deform_word_ptn[_deform_order]
                                    _deform_order += 1
                                    if _deform_order >= len(_list_deform_word_ptn):
                                        _deform_finished = True
                                    if re.search(_p[0], _fragment) is not None:
                                        _w = words_to_normal_form(_fragment, ptn=_p[0], new=_p[1])
                                        break
                                except Exception as e:
                                    _deform_finished = True
                                    print(e)
                                    break
                            _is_in = False
                            continue
                        else:
                            _is_in = False
                            break
                if _is_in:
                    if _dict_finder[_fragment] in _dict_counter:
                        _dict_counter[_dict_finder[_fragment]] += 1
                    else:
                        _dict_counter[_dict_finder[_fragment]] = 1
                else:
                    print('%-12s [X]' % _fragment)  # 不是所要

            # 输出结果
            _list_out = words_frequency_sort_list(_dict_counter)
            for _w in _list_out:
                fd_out.write(_w + '\n')
            fd_out.flush()
            print('得到:%d' % len(_list_out))

            fd_pool.close()
            fd_known.close()
            fd_in.close()
            fd_out.close()
    finally:
        if not _flag_file_exist:
            os.remove(file_known_words_pool)


def words_to_normal_form(strings, ptn, new=None):
    _bkup = strings
    _s = re.search(ptn, strings)
    while _s is not None:
        try:
            # print('%s-->%s' % (ptn, s.group()))
            if new is None:
                strings = re.sub(ptn, r'\1' + _s.group().lstrip(r'\1').lower(), strings, 1)  # 转小写
            else:
                strings = re.sub(ptn, new, strings)  # 替换
            _s = re.search(ptn, strings)
        except Exception as e:
            print('正则式发生异常，返回原字符串:', e)
            return _bkup
    try:
        del _bkup
    finally:
        return strings


def words_frequency_sort_list(dict_cnt):
    _d = dict_cnt
    _list_s = sorted(_d.items(), key=lambda x: x[1], reverse=True)  # 返回值形如:[('c', 2), ('a', 3), ('b', 7)]

    _list_tmp = []
    _prev_num = -1
    _list_ret = []
    _list_s.append((r'', -1))
    for _tu in _list_s:
        # _list_ret.append(_tu[0] + '\t\t' + str(_tu[1]))  # word+count形式
        if _prev_num != _tu[1]:
            _list_tmp = list(set(_list_tmp))
            _list_tmp.sort()
            for _w in _list_tmp:
                if len(_w) > 0:
                    _list_ret.append(_w + '\t\t' + str(_prev_num))
            _prev_num = _tu[1]
            _list_tmp = []
        _list_tmp.append(_tu[0])
    return _list_ret


# nltk还原单词得到比较准确的词汇列表
def nltk_get_wordlist(text):
    _list = []
    wnl = nltk.stem.WordNetLemmatizer()
    for word, tag in nltk.pos_tag(nltk.word_tokenize(text)):
        wntag = tag[0].lower()
        wntag = wntag if wntag in ['a', 's', 'r', 'n', 'v'] else None
        lemma = word if wntag is None else wnl.lemmatize(word, wntag)
        if not re.search(r'[^a-zA-Z]', lemma):
            _list.append(lemma)
    return _list


if __name__ == '__main__':
    main()
    print('\n===BYE===')
