import json

class Map:
    def __init__(self, tokens : dict):
        self.tokens = tokens
        self.map = {}
        self.indents_map = {}

        self.token_strings = {
            "function" : "def",
            "class" : "class"
        }

        self.executes = {}

        """"
        memory:

        index : {
            "functions" : {},
            "classes" : {}
        }
        """
        self.memory = {}

    def parse_function_args(self, tokens):
        count_tokens = len(tokens)
        args = []
        open_flag = False
        opened = 0

        for i in range(count_tokens - 1):
            token = tokens[i]
            token_type = token["name"]
            token_string = token["string"]
            token_end = token["end"]

            if token_type == "OP":
                if token_string == "(":
                    opened += 1
                elif token_string == ")":
                    opened -= 1
                
            if opened == 1:
                open_flag = True
                if token_type == "NAME":
                    args.append(token_string)
            elif opened == 2 and open_flag:
                break

        return (args, token_end)

    def generate_map(self):
        count_tokens = len(self.tokens)
        indent = 0

        for i in range(count_tokens - 1):
            last_token = None
            last_token_type = None
            last_token_string = None
            last_token_index = None

            # last token info
            if i > 0:
                last_token = self.tokens[i-1]
                last_token_type = last_token["name"]
                last_token_string = last_token["string"]
                last_token_start = last_token["start"]
                last_token_end = last_token["end"]

            next_token = None
            next_token_type = None
            next_token_string = None
            next_token_index = None

            # next token info
            if i < count_tokens - 1:
                next_token = self.tokens[i+1]
                next_token_type = next_token["name"]
                next_token_string = next_token["string"]
                next_token_start = next_token["start"]
                next_token_end = next_token["end"]

            # token info
            token = self.tokens[i]
            token_type = token["name"]
            token_string = token["string"]
            token_start = token["start"]
            token_end = token["end"]

            # detect dedent and indent
            if token_type == "INDENT":
                indent += 1
            elif token_type == "DEDENT":
                indent -= 1
            self.indents_map[token_start[0]] = indent

            # detect creates, calls and other
            if token_type == "NAME":
                
                # detect create function
                if last_token_string == self.token_strings["function"]:
                    args = self.parse_function_args(self.tokens[i:count_tokens - 1])
                    index = (last_token_start, args[1])
                    
                    if not self.memory.get(index, False):
                        self.memory[index] = {}
                    if not self.memory.get(index, False).get("functions", False):
                        self.memory[index]["functions"] = {}
                    self.memory[index]["functions"][token_string] = {
                        "args" : args[0]
                    }

            # detect other actions
            if token_type == "OP":
                if token_string == "=":
                    if next_token and last_token:
                        if next_token_type == "NAME" and last_token_type == "NAME":
                            index = (last_token_start, next_token_end)

                            call_flag = False
                            if i + 2 < count_tokens:
                                after_next = self.tokens[i+2]
                                if after_next["name"] == "OP" and after_next["string"] == "(":
                                    call_flag = True

                            # call function
                            if call_flag:
                                if not self.memory.get(index, False):
                                    self.memory[index] = {}
                                if not self.memory[index].get("calls", False):
                                    self.memory[index]["calls"] = {}
                                self.memory[index]["calls"][last_token_string] = {
                                    "function": next_token_string,
                                    "type": "call"
                                }
                            else:
                                # clone function
                                if not self.memory.get(index, False):
                                    self.memory[index] = {}
                                if not self.memory[index].get("assignments", False):
                                    self.memory[index]["assignments"] = {}
                                self.memory[index]["assignments"][last_token_string] = {
                                    "value": next_token_string,
                                    "type": "copy"
                                }

    def _get_debug(self):
        print("indents map")
        indents_map_str = {str(k): v for k, v in self.indents_map.items()}
        print(json.dumps(indents_map_str, indent=2))

        print("\nmap")
        map_str = {str(k): v for k, v in self.map.items()}
        print(json.dumps(map_str, indent=2))

        print("\nmemory")
        memory_str = {str(k): v for k, v in self.memory.items()}
        print(json.dumps(memory_str, indent=2))


            
    def _get_map(self):
        return self.map
