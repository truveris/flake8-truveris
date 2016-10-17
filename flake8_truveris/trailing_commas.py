import tokenize


OPENING_BRACKETS = [
    "[",
    "{",
    "(",
]

CLOSING_BRACKETS = [
    "]",
    "}",
    ")",
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


def get_trailing_comma_errors(file_tokens):
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
            context_errors, index = eval_context_commas(
                tokens,
                index,
            )
            errors += context_errors
        index += 1
    return errors


def eval_context_commas(tokens, context_start_index, layer=1):
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
            subcontext_errors, index = eval_context_commas(
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
                                "message": "T812 missing trailing comma",
                                "line": t.start_row,
                                "col": t.end_col,
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


def fix(file_lines, error):
    # column and line numbers are 1-indexed, so get the actual column
    # and line numbers
    comma_insert_point = error.column_number - 1
    line_number = error.line_number - 1
    # add a comma to the problematic line
    file_lines[line_number] = "{},{}".format(
        file_lines[line_number][:comma_insert_point],
        file_lines[line_number][comma_insert_point:],
    )

    return file_lines
