from pandas import read_csv
from os import walk, path, mkdir
from re import sub
from pickle import dump, load
from nltk.stem import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from ufal.udpipe import Model, Pipeline, ProcessingError

ps = PorterStemmer()
stop = stopwords.words('english')
kw_marker_1 = 'Ключевые  слова'
kw_marker_5 = 'Ключевые  слова'
kw_marker_2 = 'Key words'
kw_marker_3 = 'Ключевые слова'
kw_marker_4 = 'Keywords'
intro_marker_1 = 'Introduction'
intro_marker_2 = 'INTRODUCTION'
ref_marker_1 = 'References'
ref_marker_2 = 'REFERENCES'


def get_lang(paper_id):
    return langs.loc[langs['ID'] == paper_id, 'Lang'].values[0]


def make_alpha(files):
    files_alpha = {}
    for num, i in files.items():
        if len(i) > 0:
            text = sub('http\S+|www\S+', '', i)
            files_alpha[num] = sub('\.+', '.', sub(' \.', '.', sub(' +', ' ', sub(r'[^,.a-zA-Z -]+', '',
                                                                                  text.replace('-\n', '').replace('\n',
                                                                                                                  ' ')))))

    for a, i in files_alpha.items():
        if len(i) > 0:
            try:
                with open(path.join('..', '..', 'parsed', 'texts-en-alpha', a), 'w') as f:
                    f.write(i)
            except OSError:
                mkdir(path.join('..', '..', 'parsed', 'texts-en-alpha'))


def make_stemmed(files):
    files_stemmed = {}
    for name, file in files.items():
        files_stemmed[name] = sub('\,+', ',', sub('\.+', '.', sub(' +\.', '.', sub(' +\,', ',', sub(' +', ' ', ' '.join(
            [ps.stem(word) for word in word_tokenize(file) if word not in stop]))))))
    for a, i in files_stemmed.items():
        if len(i) > 0:
            try:
                with open(path.join('..', '..', 'parsed', 'texts-en-stemmed', a), 'w') as f:
                    f.write(i)
            except OSError:
                mkdir(path.join('..', '..', 'parsed', 'texts-en-stemmed'))


def make_lemmatized_with_udpipe(files):
    files_lemmatized = {}
    model_path = path.join('..', '..', '..', 'udpipe', 'src', 'english-2.0.udpipe')
    model = Model.load(model_path)
    pipeline = Pipeline(model, 'tokenize', Pipeline.DEFAULT, Pipeline.DEFAULT, 'conllu')
    for name, file in files.items():
        files_lemmatized[name] = pipeline.process(file)
    for a, i in files_lemmatized.items():
        if len(i) > 0:
            try:
                with open(path.join('..', '..', 'parsed', 'texts-en-lemmatized-udpipe', a), 'w') as f:
                    f.write(i)
            except OSError:
                mkdir(path.join('..', '..', 'parsed', 'texts-en-lemmatized-udpipe'))


if __name__ == '__main__':
    eng_files = {}
    eng_files_cleared = {}

    langs = read_csv(path.join('..', '..', 'parsed', 'texts', 'languages.csv'))
    for a, b, files in walk(path.join('..', '..', 'parsed', 'texts')):
        for file in files:
            if 'txt' not in file:
                continue
            if get_lang(file.split('.')[0], langs) == 'en':
                with open(a + '/' + file, 'r') as f:
                    eng_files[file] = f.read()

    for num, eng_file in eng_files.items():
        i = eng_file
        if eng_file.split(' ', 1)[0] == 'Keywords:':
            i = eng_file.split('\n\n', 1)[1]
        temp = i
        if kw_marker_2 in i:
            temp = i.split(kw_marker_2)[1].split('\n\n', 1)[1]
        elif kw_marker_4 in i:
            temp = i.split(kw_marker_4)[1].split('\n\n', 1)[1]
        else:
            temp = i
        cleartemp = temp
        if kw_marker_1 in temp:
            cleartemp = i.split(kw_marker_1)[1].split('\n\n', 1)[1]
        elif kw_marker_3 in temp:
            cleartemp = i.split(kw_marker_3)[1].split('\n\n', 1)[1]
        else:
            cleartemp = temp
        cleartemp = cleartemp.split(ref_marker_1)[0]
        cleartemp = cleartemp.split(ref_marker_1)[0]
        if cleartemp.find(intro_marker_1) > 5000:
            eng_files_cleared[num] = str(cleartemp)
            continue
        if intro_marker_1 in cleartemp:
            eng_files_cleared[num] = cleartemp.split(intro_marker_1)[1].split('\n\n', 1)[1]
        elif intro_marker_2 in cleartemp:
            eng_files_cleared[num] = cleartemp.split(intro_marker_2)[1].split('\n\n', 1)[1]
        else:
            eng_files_cleared[num] = str(cleartemp)

        for a, i in eng_files_cleared.items():
            if len(i) > 0:
                try:
                    with open(path.join('..', '..', 'parsed', 'texts-en', a), 'w') as f:
                        f.write(i)
                except OSError:
                    mkdir(path.join('..', '..', 'parsed', 'texts-en'))

        make_alpha(eng_files_cleared)
        # make_stemmed(eng_files_cleared)
        make_lemmatized_with_udpipe(eng_files_cleared)
