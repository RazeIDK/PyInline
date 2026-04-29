class Map:
    def __init__(self, tokens : dict):
        self.tokens = tokens
        self.map = {}
        self.indents_map = {}

        self.token_strings = {
            "function" : "def",
            "class" : "class"
        }

        self.memory = {
            "index" : {
                "functions" : {},
                "classes" : {}
            }
        }

        self.standart_create_function = {
            "action" : False,
            "line" : False
        }

    def parse_function_args(self, tokens):
        count_tokens = len(tokens)
        args = []
        opened = 0

        for i in range(count_tokens - 1):
            token = tokens[i]
            token_type = token["name"]
            token_string = token["string"]

            if token_type == "OP":
                if token_string == "(":
                    opened += 1
                elif token_string == ")":
                    opened -= 1
                
            if opened == 1:
                if token_type == "NAME":
                    args.append(token_string)

        return args


    def generate_map(self):
        count_tokens = len(self.tokens)
        create_function = self.standart_create_function
        indent = 0

        for i in range(count_tokens - 1):
            last_token = None
            next_token = None

            # token info
            token = self.tokens[i]
            token_type = token["name"]
            token_string = token["string"]
            token_start = token["start"]
            token_end = token["end"]
            token_index = (token_start, token_end)
            
            # get near tokens
            if i > 0:
                last_token = self.tokens[i-1]
            if i > count_tokens - 1:
                next_token = self.tokens[i+1]

            # detect dedent and indent
            if token_type == "INDENT":
                indent += 1
            elif token_type == "DEDENT":
                indent -= 1
            self.indents_map[token_index] = indent

            # detect creates, calls and other
            if token_type == "NAME":
                
                # detect create function
                if token_string == self.token_strings["function"]:
                    create_function["action"] = True
                    create_function["index"] = token_index
                
                elif create_function["action"]:
                    index = create_function["index"]
                    args = self.parse_function_args(self.tokens[i:count_tokens - 1])
                    
                    if not self.memory.get(index, False):
                        self.memory[index] = {}
                    if not self.memory.get(index, False).get("functions", False):
                        self.memory[index]["functions"] = {}
                    self.memory[index]["functions"][token_string] = {
                        "args" : args
                    }


            
    def _get_map(self):
        return self.map
