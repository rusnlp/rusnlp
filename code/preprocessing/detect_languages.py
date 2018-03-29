from langdetect import detect_langs
from os import walk, path
from pandas import DataFrame

if __name__ == "__main__":
    texts_dir = path.join('..', 'prepared-data', 'texts')
    data = {'ID':[], 'Lang':[], 'Prob':[]}

    for _, _, files in walk(texts_dir):
        for file in files[:10]:
            with open(path.join(texts_dir, file), 'r') as f:
                text = f.read()
                try:
                    lang = detect_langs(text)
                    data['ID'].append(file.split('.txt')[0])
                    data['Lang'].append(lang[0].lang)
                    data['Prob'].append(round(lang[0].prob, 2))
                except:
                    pass
    DataFrame(data).to_csv(path.join(textsdir, 'languages.csv'))
