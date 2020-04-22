## txt2json converter description

To convert articles to jsonline files to add to database you should:

* create **config.json**

Example:

```json
{
  "hash_title_url": "RusNLP/data-txt/hash_title_url.tsv",
  "name2author": "RusNLP/data-txt/current_authors.tsv",
  "name2affiliation": "RusNLP/data-txt/current_affiliations.tsv",
  "missing_authors": "RusNLP/data-txt/missing_data/missing_authors.tsv",
  "missing_affiliations": "RusNLP/data-txt/missing_data/missing_affiliations.tsv",
  "input_file": "RusNLP/data-txt/",
  "out_texts_dir": "RusNLP/data-txt/extracted_texts", (optional)
  "out_metadata_path": "RusNLP/data-txt/metadata.jsonlines"
}
```

* run:

```
python run txt2json.py config.json
```
