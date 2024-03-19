import matplotlib.pyplot as plt

from tqdm import tqdm
from tree_sitter import Parser, Language
from collections import Counter, defaultdict

from treesitter_visitor import CallExtractionVisitor
from r_utils import load_jsonls


def main():
    SPLIT = "train"
    DATA_PATH = f"./dataset/original/python/final/jsonl/{SPLIT}/"
    LANGUAGE = Language("build/python-languages.so", "python")
    parser = Parser()
    parser.set_language(LANGUAGE)

    call_counters = defaultdict(Counter)
    n_calls = defaultdict(int)
    n_files = defaultdict(int)

    objs = load_jsonls(DATA_PATH, head=100000)
    print(f"load {len(objs)} samples")

    for obj in tqdm(objs):
        repo = obj["repo"]
        code = obj["code"]
        tree = parser.parse(code.encode())
        root = tree.root_node

        visitor = CallExtractionVisitor()
        visitor.visit(root)
        calls = visitor.get_res()
        call_counters[repo].update(calls)
        n_calls[repo] += len(calls)
        n_files[repo] += 1

    for repo, counter in call_counters.items():
        print("repository:", repo)
        print("number of files:", n_files[repo])
        print("number of func calls:", n_calls[repo])
        print(f"calls per func: {n_calls[repo] / n_files[repo]:.2f}")
        print("most common calls", counter.most_common(10))
        print()

    aggregated_calls = Counter()
    for counter in call_counters.values():
        aggregated_calls.update(counter)

    print(f"Total #repos: {len(n_calls)}")
    print(f"Total #files: {sum(n_files.values())}")

    print(f"Max #files: {max(n_files.values())}")
    print(f"Min #files: {min(n_files.values())}")

    print(f"Max #calls (repowise): {max(n_calls.values())}")
    print(f"Min #calls (repowise): {min(n_calls.values())}")

    print("Most common calls:", aggregated_calls.most_common(25))

    # n_calls distribution
    fig, ax = plt.subplots()
    n_calls_list = list(n_calls[repo] / n_files[repo] for repo in n_calls.keys())
    ax.hist(n_calls_list, bins=25)

    ax.set_xlabel("#Calls per function")
    ax.set_ylabel("#Repositories")

    fig.savefig(f"./figs/{SPLIT}_n_calls.png")

    # top 10 calls
    fig, ax = plt.subplots()
    top_calls = aggregated_calls.most_common(15)
    top_calls, counts = zip(*top_calls)
    bars = ax.barh(
        top_calls,
        counts,
        color="blue",
        alpha=0.5,
    )
    ax.set_xlabel("#Calls")
    ax.set_yticks(top_calls)
    ax.set_yticklabels(top_calls)
    ax.invert_yaxis()
    ax.set_title("Top 15 calls")

    # annotate
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 1,
            bar.get_y() + bar.get_height() / 2,
            f"{width}",
            va="center",
        )
    fig.tight_layout()
    fig.savefig(f"./figs/{SPLIT}_top_calls.png")


if __name__ == "__main__":
    main()
