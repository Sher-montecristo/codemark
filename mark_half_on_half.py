import os
import pickle
import tqdm
import json
import argparse

# from codemarker.java import JavaCodeMarkder
from codemarker import CodeMarker
from tree_sitter import Parser, Language
import sys

sys.setrecursionlimit(500)


def load_jsonl(data_path):
    with open(data_path, "r") as f:
        json_strs = f.readlines()
    json_objs = [json.loads(jstr)["code"] for jstr in json_strs]
    return json_objs


def load_pickle(data_path):
    with open(os.path.join(data_path), "rb") as f:
        pickle_list = pickle.load(f)
    if isinstance(pickle_list, dict):
        pickle_list = pickle_list["code"]
    return pickle_list


def load_data(args, parser):
    data_path = args.data_path
    data = []
    if os.path.isdir(data_path):
        for file in os.listdir(data_path):
            if file.endswith("jsonl"):
                data.extend(load_jsonl(os.path.join(data_path, file)))
            else:
                data.extend(load_pickle(os.path.join(data_path, file)))
    else:
        if data_path.endswith("jsonl"):
            data.extend(load_jsonl(data_path))
        else:
            data.extend(load_pickle(data_path))

    print(f"{len(data)} data loaded!")
    parsed = []
    code = []
    for item in tqdm.tqdm(data, desc="parse ast"):
        try:
            parsed.append(parser.parse(bytes(item, encoding="utf-8")))
            code.append(item)
        except SyntaxError:
            continue
    print(
        f"AST Parse: {len(data) - len(parsed)} failed, {len(parsed)} left, {len(parsed)/len(data)} success rate"
    )
    return parsed, code


def args_parse():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--language", type=str)
    arg_parser.add_argument("--dataset_name", type=str)
    arg_parser.add_argument("--data_path", type=str)
    arg_parser.add_argument("--get_popularity", action="store_true")
    args = arg_parser.parse_args()
    return args


if __name__ == "__main__":
    # currently available SPTs are specified in config.py of each language
    # java: unequal_null, is_empty, init_string, index_of, if_else_return, self_add, not, equal_false
    # python: call, initlist, range, items, print, list
    # select two SPTs to construct backdoors
    # for example:
    java_backdoors = [
        [["unequal_null", "is_empty"]],
        [["init_string", "index_of"]],
    ]
    python_backdoors = [
        [["call", "print"]],
        [["initlist", "range"]],
    ]
    mark_rates = [1.0]  # proportion of marked samples in the dataset

    args = args_parse()
    if args.language == "python":
        LANGUAGE = Language("build/python-languages.so", "python")
        backdoors = python_backdoors
    elif args.language == "java":
        LANGUAGE = Language("build/java-languages.so", "java")
        backdoors = java_backdoors
    parser = Parser()
    parser.set_language(LANGUAGE)
    parsed, code = load_data(args, parser)

    os.makedirs(f"./dataset/{args.language}", exist_ok=True)

    total_codes = len(code)
    n_1 = int(total_codes / 2)
    n_2 = total_codes - n_1

    code_1 = code[:n_1]
    code_2 = code[n_1:]
    parsed_1 = parsed[:n_1]
    parsed_2 = parsed[n_1:]

    rewriter_1 = CodeMarker(parsed_1, code_1, args.language)
    rewriter_2 = CodeMarker(parsed_2, code_2, args.language)

    full_rewriten = []
    full_test = []
    full_actual = []
    for i, rewriter in enumerate([rewriter_1, rewriter_2]):
        backdoor = backdoors[i]

        if backdoor == []:
            raise ValueError

        rewriten, test_set, actual, stat = rewriter.rewrite(mark_rates, backdoor)

        if i == 0:
            full_rewriten = rewriten
        else:
            for j, r in enumerate(rewriten):
                for key in r:
                    full_rewriten[j][key].extend(r[key])

        full_test.extend(test_set)
        full_actual.extend(actual)

        print(len(test_set), len(actual))
        print(stat)

    print(len(full_rewriten[1]["all_blobs"]))
    print(len(full_test))
    print(len(full_actual))

    for n, ret in enumerate(full_rewriten):
        mark_name = "0" if n == 0 else f"{int(mark_rates[n-1]*100)}"
        with open(
            f"./dataset/{args.language}/{args.dataset_name}_b_{mark_name}.pickle",
            "wb",
        ) as f:
            pickle.dump(ret, f)
    with open(f"./dataset/{args.language}/{args.dataset_name}_b_test.jsonl", "w") as f:
        for item in full_test:
            f.write(json.dumps(item) + "\n")

    with open(
        f"./dataset/{args.language}/{args.dataset_name}_b{i+1}_actual.jsonl",
        "w",
    ) as f:
        for item in full_actual:
            f.write(json.dumps({"code": item}) + "\n")
