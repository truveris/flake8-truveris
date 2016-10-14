import tokenize


def get_inline_comment_errors(file_tokens):
    errors = []
    token_num = len(file_tokens)
    index = 0
    while index < token_num:
        token = file_tokens[index]
        if token.type == tokenize.COMMENT:
            # current token is a comment
            previous_token = file_tokens[index - 1]
            if previous_token.type not in (tokenize.NL, tokenize.NEWLINE):
                # previous token is a not new line therefore comment is inline
                error_msg = {
                    "message": "T568 no inline comments",
                    "line": token.start_row,
                    "col": token.start_col,
                }
                errors.append(error_msg)
        index += 1

    return errors
