#!/usr/bin/env python3
# coding: utf-8

import argparse
import pandas as pd


class DoubleError(Exception):
    pass


def merge_annotations(current_file, updated_file, result_name="my_result.tsv"):
    """
    Merging annotated authors\affiliations with the current dataset.
    It is recommended to assign the output file the .tsv extension.
    """

    old_df = pd.read_csv(
        current_file, sep="\t", names=["index", "dict_name", "name_variants"]
    )
    new_df = pd.read_csv(
        updated_file, sep="\t", names=["text", "name_variants", "index", "dict_name"]
    )
    format_new_df = new_df[["index", "dict_name", "name_variants"]]

    merged_df = pd.concat([old_df, format_new_df])
    merged_df.sort_values("index")

    for i in set(merged_df["index"]):
        temp_df = merged_df[merged_df["index"] == i]
        if len(set(temp_df["dict_name"])) > 1:
            raise DoubleError(
                f"Different affiliations/authors with same id occurred!"
                f"Please, check {set(temp_df['dict_name'])}"
                f"id: {i} "
            )
    merged_df = merged_df.sort_values(by=["index"])
    if True in merged_df.duplicated():
        print("Attention, duplicates in data frame!")
        print(merged_df[merged_df.duplicated(keep=False)], 'Duplicates will be deleted automatically')
        merged_df = merged_df.drop_duplicates()
    if result_name:
        merged_df.to_csv(result_name, index=False, sep="\t", header=None)

    return merged_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    arg = parser.add_argument
    arg(
        "--current_file",
        "-c",
        help="Path to current affiliations or authors",
        type=str,
        default="current_affiliations.tsv",
        required=True,
    )
    arg("--new_file", "-n", help="Path to annotated file", type=str, required=True)
    arg(
        "--result_file",
        "-r",
        help="You can add result file name (path), result.tsv by default. ",
        type=str,
        default="result.tsv",
        required=False,
    )

    args = parser.parse_args()
    old_file = args.current_file
    new_file = args.new_file
    result_file = args.result_file

    new_data = merge_annotations(old_file, new_file, result_name=result_file)

    print(f"Updated dataset saved to {result_file}")
