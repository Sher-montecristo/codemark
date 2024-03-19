from tqdm import tqdm
from tree_sitter import Parser, Language
from collections import defaultdict

from treesitter_visitor import NaiveAverageVisitor
from r_utils import load_jsonls


def main():
    SPLIT = "train"
    DATA_PATH = f"./dataset/original/python/final/jsonl/{SPLIT}/"
    LANGUAGE = Language("build/python-languages.so", "python")
    parser = Parser()
    parser.set_language(LANGUAGE)

    n_occurrences = defaultdict(int)
    n_files = defaultdict(int)

    objs = load_jsonls(DATA_PATH, head=100000)
    print(f"load {len(objs)} samples")

    for obj in tqdm(objs):
        repo = obj["repo"]
        code = obj["code"]
        tree = parser.parse(code.encode())
        root = tree.root_node

        visitor = NaiveAverageVisitor()
        visitor.visit(root)
        naive_avgs = visitor.get_res()
        n_occurrences[repo] += len(naive_avgs)
        n_files[repo] += 1

    for repo in n_occurrences.keys():
        print("repository:", repo)
        print("number of files:", n_files[repo])
        print("number of list inits:", n_occurrences[repo])
        print(f"list inits per func: {n_occurrences[repo] / n_files[repo]:.2f}")
        print()

    print(f"Total #repos: {len(n_occurrences)}")
    print(f"Total #files: {sum(n_files.values())}")

    print(f"Max #files: {max(n_files.values())}")
    print(f"Min #files: {min(n_files.values())}")

    print(f"Max #occurrences (repowise): {max(n_occurrences.values())}")
    print(f"Min #occurrences (repowise): {min(n_occurrences.values())}")

    print(f"Total #occurrences: {sum(n_occurrences.values())}")
    print(
        f"Average #occurrences: {sum(n_occurrences.values()) / sum(n_files.values()):.2f}"
    )


if __name__ == "__main__":
    main()
