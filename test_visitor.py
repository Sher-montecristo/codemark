from r_utils import pprint_tree
from tree_sitter import Parser, Language
from treesitter_visitor import NaiveSumVisitor


def main():
    LANGUAGE = Language("build/python-languages.so", "python")
    parser = Parser()
    parser.set_language(LANGUAGE)

    code = """
    for project in glob.glob(os.path.join(dir, '*.uproject')):
        return os.path.realpath(project)
    """

    tree = parser.parse(code.encode())
    root = tree.root_node

    print(code)
    pprint_tree(root)

    visitor = NaiveSumVisitor()
    visitor.visit(root)

    for i, res in enumerate(visitor.get_res()):
        print(f"Instance #{i}")
        print(res)


if __name__ == "__main__":
    main()
