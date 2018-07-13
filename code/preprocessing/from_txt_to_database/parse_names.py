from transliterate import translit
from re import match
from os import path
from collections import defaultdict


def replace_initials(name):
    initials = name.split('.')
    for i, initial in enumerate(initials[::-1]):
        if i > 0:
            yield(initial.strip() + '.')
        else:
            yield(initial.strip())


def detect_lang(name):
    if match('[A-z]', name):
        return name
    else:
        return translit(name, language_code='ru', reversed=True)


if __name__ == '__main__':
    names = []
    with open('names.txt', 'r') as f:
        names = f.read().split('\n')
    new_names = defaultdict(lambda: [])

    for name_raw in names[:59]:
        name = name_raw.strip()
        new_names[' '.join(name_raw.strip().split(' ')[::-1])].append(name)

    for name_raw in names[59:65]:
        name = name_raw.strip()
        try:
            if name[1] == '.':
                new_names[' '.join(list(replace_initials(detect_lang(name))))].append(name)
            else:
                new_names[detect_lang(name)].append(name)
        except IndexError:
            pass

    for name_raw in names[65:93]:
        name = name_raw.strip()
        new_names[' '.join(name_raw.strip().split(' ')[::-1])].append(name)

    for name_raw in names[93:96]:
        new_names[name_raw].append(name_raw)

    for name in names[96:167]:
        new_names[' '.join(name.strip().split(' ')[::-1])].append(name)

    for name in names[167:172]:
        new_names[' '.join(translit(name, language_code='ru', reversed=True).strip().split(' ')[::-1])].append(name)

    for name in names[172:178]:
        new_names[translit(name, language_code='ru', reversed=True)].append(name)

    for name_raw in names[178:183]:
        name = name_raw.replace('\xa0', '')
        new_names[' '.join(translit(name, language_code='ru', reversed=True).strip().split(' ')[::-1])].append(name)

    for name_raw in names[183:186]:
        name = name_raw.strip()
        try:
            if name[1] == '.':
                new_names[' '.join(list(replace_initials(detect_lang(name))))].append(name)
            else:
                new_names[detect_lang(name)].append(name)
        except IndexError:
            pass

    for name in names[186:188]:
        new_names[' '.join(translit(name, language_code='ru', reversed=True).strip().split(' ')[::-1])].append(name)

    for name in names[188:229]:
        new_names[' '.join(name.strip().split(' ')[::-1])].append(name)

    for name_raw in names[230:236]:
        name = name_raw.strip()
        try:
            if name[1] == '.':
                new_names[' '.join(list(replace_initials(detect_lang(name))))].append(name)
            else:
                new_names[detect_lang(name)].append(name)
        except IndexError:
            pass

    for name in names[236:285]:
        new_names[' '.join(name.strip().split(' ')[::-1])].append(name)

    for name_raw in names[285:288]:
        name = name_raw.strip()
        try:
            if name[1] == '.':
                new_names[' '.join(list(replace_initials(detect_lang(name))))].append(name)
            else:
                new_names[detect_lang(name)].append(name)
        except IndexError:
            pass

    for name in names[288:304]:
        new_names[' '.join(name.strip().split(' ')[::-1])].append(name)

    for name in names[304:313]:
        new_names[translit(name, language_code='ru', reversed=True)].append(name)

    for name in names[313:320]:
        new_names[' '.join(name.strip().split(' ')[::-1])].append(name)

    for name in names[320:1263]:
        new_names[detect_lang(name)].append(name)

    for name_raw in names[1263:1388]:
        name = name_raw.strip()
        try:
            if name[1] == '.':
                new_names[' '.join(list(replace_initials(detect_lang(name))))].append(name)
            else:
                new_names[detect_lang(name)].append(name)
        except IndexError:
            pass

    for name in names[1388:]:
        new_names[detect_lang(name)].append(name)

    with open(path.join('data', 'new_names.txt'), 'w') as f:
        for i,k  in sorted(new_names.items()):
            f.write('{}: [{}]\n'.format(i, ', '.join(k)))
