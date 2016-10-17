import tokenize


def get_inline_comment_errors(file_tokens):
    errors = []
    token_num = len(file_tokens)
    # first token in file can't be inline comment
    index = 1
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


def fix(file_lines, error):
    # column and line numbers are 1-indexed, so get the actual column
    # and line numbers
    comment_start_point = error.column_number - 1
    line_number = error.line_number - 1

    full_line = file_lines[line_number]
    comment = full_line[comment_start_point:]
    # strip the comment from the line
    line_without_comment = full_line[:comment_start_point]
    # strip the trailing whitespace from the line (keep the new line though)
    formatted_line = "{}\n".format(line_without_comment.rstrip())
    # replace the old line with this line
    file_lines[line_number] = formatted_line

    # construct the line to be used for the comment
    comment_line = "{indentation}{comment}".format(
        indentation=formatted_line[:-len(formatted_line.lstrip())],
        comment=comment,
    )

    # insert the comment line just before the formatted line
    file_lines.insert(line_number, comment_line)

    return file_lines
