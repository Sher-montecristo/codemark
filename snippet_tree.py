from r_utils import pprint_tree
from tree_sitter import Parser, Language


def main():
    LANGUAGE = Language("build/python-languages.so", "python")
    parser = Parser()
    parser.set_language(LANGUAGE)

    code = """
    mysum = 0
    for i in range(10):
        mysum = mysum + i
    """

    print(code)
    pprint_tree(parser.parse(code.encode()).root_node)


if __name__ == "__main__":
    main()
