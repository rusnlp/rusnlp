from sklearn.cluster import AffinityPropagation
from distance import levenshtein
from collections import defaultdict
import numpy as np
import json


def make_clusters(words_list):
    parsed_clusters = defaultdict(lambda: [])
    words = np.asarray(words_list) 
    lev_similarity = -1*np.array([[levenshtein(w1,w2) for w1 in words] for w2 in words])
    affprop = AffinityPropagation(affinity='precomputed', damping=0.5)
    affprop.fit(lev_similarity)
    for cluster_id in np.unique(affprop.labels_):
        exemplar = words[affprop.cluster_centers_indices_[cluster_id]]
        cluster = np.unique(words[np.nonzero(affprop.labels_==cluster_id)])
        parsed_clusters[exemplar] = list(cluster)
    return dict(parsed_clusters)


def serialize_data(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4, sort_keys=True)
  

if __name__ == '__main__':
    with open('affiliations.pickle', 'rb') as f:
        affiliations = load(f)

    with open('authors_list.pickle', 'rb') as f:
        authors = load(f)
    serialize_data(make_clusters(list(authors['en'])), 'authors-en.json')
    serialize_data(make_clusters(list(authors['ru'])), 'authors-ru.json')
    serialize_data(make_clusters(list(affiliations['en'])), 'affiliations-en.json')
    serialize_data(make_clusters(list(affiliations['ru'])), 'affiliations-ru.json')
    
