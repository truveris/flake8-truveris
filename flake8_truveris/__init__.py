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


__version__ = '0.1.0'

OPENING_BRACKETS = [
    '[',
    '{',
    '(',
]

CLOSING_BRACKETS = [
    ']',
    '}',
    ')',
]


class Token(object):
    '''Python 2 and 3 compatible token'''
    def __init__(self, token):
        self.token = token

    @property
    def type(self):
        return self.token[0]

    @property
    def string(self):
        return self.token[1]

    @property
    def start(self):
        return self.token[2]

    @property
    def start_row(self):
        return self.token[2][0]

    @property
    def start_col(self):
        return self.token[2][1]

    @property
    def end_col(self):
        return self.token[3][1]


class CheckTruveris(object):

    name = 'flake8-truveris'
    version = __version__

    def __init__(self, tree, filename='(none)', builtins=None):
        self.tree = tree
        self.filename = filename

    def get_file_contents(self):
        if self.filename in ('stdin', '-', None):
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
            if token.type == tokenize.COMMENT
            and token.string.endswith('noqa')
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

        trailing_comma_errors = self.get_trailing_comma_errors(file_tokens)
        errors += trailing_comma_errors

        errors = sorted(errors, key=lambda k: k["line"])

        for error in trailing_comma_errors:
            yield (
                error['line'],
                error['col'],
                error['message'],
                type(self),
            )

    def get_trailing_comma_errors(self, file_tokens):
        # strip comment tokens to simplify logic
        errors = []
        tokens = [
            token
            for token
            in file_tokens
            if token.type != tokenize.COMMENT
        ]
        token_num = len(tokens)
        index = 0
        while index < token_num:
            if tokens[index].string in OPENING_BRACKETS:
                context_errors, index = self.evaluate_potential_comma_contexts(
                    tokens,
                    index,
                )
                errors += context_errors
            index += 1
        return errors

    def evaluate_potential_comma_contexts(self, tokens, context_start_index):
        errors = []
        opener = tokens[context_start_index].string
        closer = CLOSING_BRACKETS[OPENING_BRACKETS.index(opener)]
        context_uses_commas = False
        context_end_index = None

        index = context_start_index + 1

        while index < len(tokens):
            t = tokens[index]
            if t.string in OPENING_BRACKETS:
                subcontext_errors, index = self.evaluate_potential_comma_contexts(
                    tokens,
                    index,
                )
                errors += subcontext_errors
                continue
            elif (
                t.string == "," and
                tokens[index + 1].type == tokenize.NL and
                context_uses_commas is False):
                # if any value in the data structure ends the line with a
                # comma, all values should, so start over and make sure.
                context_uses_commas = True
                index = context_start_index + 1
                continue
            elif (tokens[index + 1].type == tokenize.NL and
                    context_uses_commas and
                    t.string != ","):
                # should end with a comma, but does not
                error_msg = {
                    'message': 'T812 missing trailing comma',
                    'line': t.start_row,
                    'col': t.end_col,
                }
                errors.append(error_msg)
            elif t.string == closer:
                # context is closing
                context_end_index = index
                break
            index += 1

        return errors, context_end_index
