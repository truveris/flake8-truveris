import tokenize
from flake8.formatting import base

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

# all the Python keywords that could prefix a parenthesis context, where
# trailing commas are either not allowed, or would change what the context gets
# evaluated as if a trailing comma were present
context_prefix_keywords = (
    "and",
    "as",
    "assert",
    "del"
    "elif",
    "exec",
    "for",
    "if",
    "in",
    "is",
    "lambda",
    "not",
    "or",
    "print",
    "raise",
    "return",
    "while",
    "with",
    "yield",
)


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
                context_errors, index = self.eval_context_commas(
                    tokens,
                    index,
                )
                errors += context_errors
            index += 1
        return errors

    def eval_context_commas(self, tokens, context_start_index, layer=1):
        errors = []
        context_end_index = None
        closing_bracket_is_end_of_value = False
        is_comprehension_context = False
        opening_bracket = tokens[context_start_index].string
        context_uses_commas = True
        if opening_bracket == "(":
            # might not be just a tuple
            context_prefix = tokens[context_start_index - 1]
            if context_prefix.type == tokenize.NAME:
                # might be a class/method/function call or definition
                if context_prefix.string in context_prefix_keywords:
                    # definitely not a class/method/function call or
                    # definition, so check for commas in context before trying
                    # to enforce a trailing comma to make sure the context is
                    # evaluated as originally written
                    context_uses_commas = False
                else:
                    # definitely a class/method/function call or definition, so
                    # trailing commas should definitely be used
                    pass
            elif context_prefix.string in ("]", ")"):
                # previous expression is evaluating to method/function, and
                # method/function calls should have trailing commas
                pass
            else:
                # definitely not a class/method/function call or
                # definition, so check for commas in context before trying to
                # enforce a trailing comma to make sure the context is
                # evaluated as originally written
                context_uses_commas = False

        index = context_start_index + 1
        previous_token = tokens[index - 1]
        while index < len(tokens):
            t = tokens[index]
            if t.string in OPENING_BRACKETS:
                # if an opening bracket is found, it means there is a context
                # within this one that must be evaluated independantly
                subcontext_errors, index = self.eval_context_commas(
                    tokens,
                    index,
                    layer=(layer + 1),
                )
                errors += subcontext_errors
                # the closing bracket for the nested context should be
                # evaluated as the end of an entry in the list/tuple/dict
                closing_bracket_is_end_of_value = True
                continue
            elif t.string in CLOSING_BRACKETS:
                # found closing bracket for a context
                if not closing_bracket_is_end_of_value:
                    # context is closing
                    context_end_index = index
                    break

            if t.type == tokenize.NAME and t.string == "for":
                # this context layer is some form of comprehension, and
                # shouldn't have its commas validated
                is_comprehension_context = True

            if t.string == ",":
                # found a comma, so enforce trailing comma usage
                context_uses_commas = True

            if tokens[index + 1].type == tokenize.NL:
                # this token is the last token on the line
                if t.string == ",":
                    # found a line that properly ends with a comma
                    pass
                else:
                    # found a line that does not end with a comma
                    if tokens[index + 2].string in CLOSING_BRACKETS:
                        # this is the last item in the context
                        if context_uses_commas:
                            # the last item in the context should have a
                            # trailing comma
                            if is_comprehension_context:
                                # should not be validating trailing commas in
                                # comprehension context
                                pass
                            elif previous_token.string in ("*", "**"):
                                # expansion can't be followed by a trailing
                                # comma
                                pass
                            else:
                                # should have a trailing comma, but doesn't
                                error_msg = {
                                    'message': 'T812 missing trailing comma',
                                    'line': t.start_row,
                                    'col': t.end_col,
                                    "layer": layer,
                                }
                                errors.append(error_msg)
                        else:
                            # context does not use commas
                            pass
                    else:
                        # only check the last entry in the context, as placing
                        # a comma anywhere else would likely alter how the
                        # list/tuple/dict gets evaluated
                        pass
            else:
                # not the last token on the line
                pass

            closing_bracket_is_end_of_value = False
            index += 1
            previous_token = t

        if is_comprehension_context:
            # shouldn't validate commas in this context, so strip the errors
            # for it
            errors = [e for e in errors if e["layer"] != layer]

        return errors, context_end_index


class FormatTruveris(base.BaseFormatter):

    error_format = "%(path)s:%(row)d:%(col)d: %(code)s %(text)s"

    def format(self, error):
        return self.error_format % {
            "code": error.code,
            "text": error.text,
            "path": error.filename,
            "row": error.line_number,
            "col": error.column_number,
        }

    def handle(self, error):
        """Handle an error reported by Flake8.
        This defaults to calling :meth:`format`, :meth:`show_source`, and
        then :meth:`write`. To extend how errors are handled, override this
        method.
        :param error:
            This will be an instance of :class:`~flake8.style_guide.Error`.
        :type error:
            flake8.style_guide.Error
        """
        line = self.format(error)
        source = self.show_source(error)
        self.write(line, source)
        if error.code == "T812":
            # column and line numbers are 1-indexed, so get the actual column
            # and line numbers
            comma_insert_point = error.column_number - 1
            line_number = error.line_number - 1

            # add a comma to the problematic line
            with open(error.filename, 'r') as file:
                # read a list of lines into data
                data = file.readlines()

            data[line_number] = "{},{}".format(
                data[line_number][:comma_insert_point],
                data[line_number][comma_insert_point:],
            )

            with open(error.filename, 'w') as file:
                file.writelines(data)
