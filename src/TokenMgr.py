import tokenize
import io
import token

class Manager:
    def __init__(self, source_code : str):
        self.source_code = source_code
        self.tokens = self.generate_tokens()

    def generate_tokens(self):
        buffer  = io.StringIO(self.source_code)
        gen_tokens = tokenize.generate_tokens(buffer.readline)
        local_tokens = []

        for t in gen_tokens:
            local_tokens.append(
                {
                    "type" : t.type,
                    "name" : token.tok_name[t.type],
                    "string" : t.string,
                    "start" : t.start,
                    "end" : t.end,
                    "line" : t.line
                }
            )

        return local_tokens

    def print_tokens(self):
        for i in self.tokens:
            print(i)

    def _get_tokens(self):   
        return self.tokens
