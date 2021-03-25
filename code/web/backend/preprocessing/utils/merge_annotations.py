import argparse
import sys
import pandas as pd

class DoubleError(Exception):
    pass

def merge_annotations():
    """
    Merging annotated authors\affilations with previous result.
    It is better to make result name with .tsv format.
    """
    # old_file, new_file, result_name = sys.argv[1:]

    parser = argparse.ArgumentParser()
    arg = parser.add_argument
    arg("--current_file", "-c", help="Path to current affiliations or authors", required=True)
    arg("--new_file", "-n", help="Path to annotated file", required=True)
    arg("--result_file", "-r", help="Add result file name", required=True)

    args = parser.parse_args()
    old_file = args.current_file
    new_file = args.new_file
    result_name = args.result_file

    old_df = pd.read_csv(old_file, sep='\t', names=['index', 'dict_name', 'name_variants'])
    new_df = pd.read_csv(new_file, sep='\t', names=['text', 'name_variants', 'index', 'dict_name'])
    format_new_df = new_df[['index', 'dict_name', 'name_variants']]

    merged_df = pd.concat([old_df, format_new_df])
    merged_df.sort_values('index')

    for i in set(merged_df['index']):
        pass
        temp_df = merged_df[merged_df['index'] == i]
        if len(set(temp_df['dict_name'])) > 1:
            raise DoubleError(f"Different affilations/authors with same id occured!"
                              f"Please, check {set(temp_df['dict_name'])}"
                              f"id: {i} ")

    merged_df.to_csv(result_name, index=False, sep ='\t')


if __name__ == '__main__':
    merge_annotations()
    # python3 merge_annotations.py current_affiliations.tsv missing_data_missing_affiliations_2021.tsv my_res.tsv