#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import MeCab
import re
import random
from collections import Counter


def text_format(text):
    '''
    文章の整形
        第１引数：文章
    「」は取り除く
    '''
    text = re.sub('[「|」|\n]', '', text)
    text = text.replace('。', '。\n')
    return text


class marcov_chain_model(object):
    def __init__(self, n_order=3):
        self.n_order = n_order
        self.dic = Counter()  # 列の辞書
        self.chain_dic = {}  # 各グループが出る順番
        self.begin_list = set([])  # 文章のはじまりの単語を集めたリスト
        self.end_list = set([])  # 最後の一文だけを集める
        self.tokenizer = MeCab.Tagger("-Ochasen")

    def _text_tokenize(self, text):
        '''
        文章をわかち書きする
            第１引数：文章
            第２引数：何階のマルコフ連鎖か
        各行の文章のリストを返す
        '''
        text_results = []
        max_len = 0
        for t in text.split():
            result = self._mecab_tokenize(t)
            sent = (['<sos>'] * (self.n_order-1)) + result + ['<eos>']
            max_len = max(max_len, len(sent))
            text_results.append(sent)
        self.chain_dic = {i: [] for i in range(max_len)}
        return text_results

    def _mecab_tokenize(self, text):
        '''
        mecabで形態素解析
            第１引数：形態素解析器（mecab）
            第２引数：文章
        分かち書きの結果を返す
        '''
        token = self.tokenizer.parse(text)
        result = []
        for t in token.split('\n'):
            surface = t.split('\t')[0]
            if surface == 'EOS' or len(surface) == 0:
                continue
            result.append(t.split('\t')[0])
        return result

    def make_dic(self, text):
        '''
        辞書と文章のはじまりを集めたリストを作成
            第１引数：分かち書きの結果
            第２引数：何階のマルコフ連鎖か
        '''
        result = self._text_tokenize(text)
        for row in result:
            for i in range(len(row)):
                if len(row[i:i+self.n_order]) < self.n_order:
                    continue
                self.dic[tuple(row[i:i+self.n_order])] += 1
                self.chain_dic[i].append(tuple(row[i:i+self.n_order]))
                if self.n_order == 1:
                    if i == 0:
                        self.begin_list.add(tuple(row[i]))
                    elif i == len(row)-2:
                        self.end_list.add(tuple(row[i]))
                elif row[i:i+self.n_order-1] == ['<sos>'] * (self.n_order-1):
                    self.begin_list.add(tuple(row[i:i+self.n_order]))

    def marcov(self, begin_word=None):
        '''
        文章の生成
            第１引数：何階のマルコフ連鎖か
            第２引数：始まりの単語、指定が無ければbegin_listから取ってくる
        文章生成の結果を出力
        '''
        if tuple(['<sos>'] * (self.n_order-1) + [begin_word])\
           not in self.begin_list and begin_word is not None:
            raise ValueError("別の単語を選んで下さい。")
        if begin_word is not None:
            before = tuple(['<sos>'] * (self.n_order-1) + [begin_word])
        else:
            before = (random.sample(self.begin_list, k=1)[0])

        # マルコフ連鎖で生成した文書を入れる
        sentence = before[self.n_order-1] + ' '

        # chain_dicのキー
        index = 1

        while sentence.find('<eos>') == -1 and before not in self.end_list:
            after_list = []
            num = 1
            for row in self.chain_dic[index]:
                if before[1:self.n_order] == row[0:self.n_order-1]:
                    if num < self.dic[row]:
                        after_list = []
                        after_list.append(row)
                        num = self.dic[row]
                    else:
                        after_list.append(row)
            before = random.choice(after_list)
            sentence += before[self.n_order-1] + ' '
            index += 1
        print(re.sub('[<eos>|\s]', '', sentence))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--text',
                        help='テキストの指定',
                        default=None)
    parser.add_argument('-n', '--n_order',
                        help='何階のマルコフ連鎖をするか（デフォルトは3階）',
                        default=3,
                        type=int)
    parser.add_argument('-w', '--word',
                        help='最初に始める単語（デフォルトはNone）',
                        type=str,
                        default=None)
    args = parser.parse_args()

    if args.text is None:
        raise ValueError("textを指定して下さい。")

    if args.n_order < 1:
        raise ValueError('n_orderは1以上を指定して下さい。')

    model = marcov_chain_model(args.n_order)

    with open(args.text, 'r') as f:
        text = f.read()

    text = text_format(text)
    model.make_dic(text)
    model.marcov(begin_word=args.word)


if __name__ == '__main__':
    main()
