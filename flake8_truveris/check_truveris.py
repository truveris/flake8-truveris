import tokenize

try:
    from flake8.engine import pep8
    stdin_get_value = pep8.stdin_get_value
    readlines = pep8.readlines
except ImportError:
    from flake8 import utils
    import pycodestyle
    stdin_get_value = utils.stdin_get_value
    readlines = pycodestyle.readlines

from flake8_truveris.token import Token
from flake8_truveris.trailing_commas import get_trailing_comma_errors
from flake8_truveris.inline_comments import get_inline_comment_errors


class CheckTruveris(object):

    name = "flake8-truveris"
    version = "0.3.1"

    def __init__(self, tree, filename="(none)", builtins=None):
        self.tree = tree
        self.filename = filename

    def get_file_contents(self):
        if self.filename in ("stdin", "-", None):
            return stdin_get_value().splitlines(True)
        else:
            return readlines(self.filename)

    def get_file_tokens(self, file_contents):
        return [
            Token(token)
            for token
            in tokenize.generate_tokens(lambda L=iter(file_contents): next(L))
        ]

    def get_noqa_line_numbers(self, file_tokens):
        return [
            token.start_row
            for token in file_tokens
            if token.type == tokenize.COMMENT and
            token.string.endswith("noqa")
        ]

    def get_qa_file_tokens(self):
        file_contents = self.get_file_contents()
        file_tokens = self.get_file_tokens(file_contents)
        noqa_line_numbers = self.get_noqa_line_numbers(file_tokens)
        # strip noqa lines
        return [
            token
            for token
            in file_tokens
            if token.start_row not in noqa_line_numbers
        ]

    def run(self):
        file_tokens = self.get_qa_file_tokens()
        errors = []

        errors += get_trailing_comma_errors(file_tokens)
        errors += get_inline_comment_errors(file_tokens)

        for e in errors:
            yield (
                e["line"],
                e["col"],
                e["message"],
                type(self),
            )
