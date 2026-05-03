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

    def parse_function_args(self, tokens, is_call=False):
        count_tokens = len(tokens)
        args = []
        current_arg = ""
        paren_depth = 0
        bracket_depth = 0
        token_end = None
        in_string = False
        
        i = 0
        while i < count_tokens:
            token = tokens[i]
            token_type = token["name"]
            token_string = token["string"]
            token_end = token["end"]
            
            if token_string == "(" and paren_depth == 0:
                paren_depth = 1
                i += 1
                continue
            
            if paren_depth == 0:
                i += 1
                continue
            
            if token_string == ")" and paren_depth == 1:
                if current_arg.strip():
                    args.append(self._parse_single_arg(current_arg.strip(), is_call))
                break
            
            if token_type == "OP":
                if token_string in "([{":
                    bracket_depth += 1
                    current_arg += token_string
                elif token_string in ")]}":
                    bracket_depth -= 1
                    current_arg += token_string
                elif token_string == "," and bracket_depth == 0 and not in_string:
                    args.append(self._parse_single_arg(current_arg.strip(), is_call))
                    current_arg = ""
                else:
                    current_arg += token_string
            elif token_type in ["NAME", "NUMBER", "STRING"]:
                current_arg += token_string
            elif token_type not in ["INDENT", "DEDENT", "NEWLINE", "NL"]:
                current_arg += token_string
            
            i += 1
        
        return (args, token_end)

    def build_blocks(self):
        blocks = {}
        current_block = []
        last_indent = 0

        for i, token in enumerate(self.tokens):
            line_num = token["start"][0]
            current_indent = self.indents_map.get(line_num, 0)

            if current_indent > last_indent:
                blocks[line_num] = {
                    "type": "block_start",
                    "indent": current_indent,
                    "parent": last_indent
                }
            elif current_indent < last_indent:
                blocks[line_num] = {
                    "type": "block_end",
                    "indent": current_indent
                }

            last_indent = current_indent

        return blocks

    def build_flow_graph(self):
        graph = {}
        prev_line = None
        prev_indent = 0

        for line_num, indent in sorted(self.indents_map.items()):
            if prev_line is None:
                prev_line = line_num
                prev_indent = indent
                continue

            edge = (prev_line, line_num)

            if indent > prev_indent:
                graph[edge] = "start"
            elif indent < prev_indent:
                graph[edge] = "end"
            else:
                graph[edge] = "line"

            prev_line = line_num
            prev_indent = indent

        return graph

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

            """# detect creates, calls and other
            if token_type == "NAME":
                
                # detect create function
                if last_token_string == self.token_strings["function"]:
                    paren_pos = -1
                    for j in range(i, count_tokens):
                        if self.tokens[j]["name"] == "OP" and self.tokens[j]["string"] == "(":
                            paren_pos = j
                            break
                        
                    if paren_pos != -1:
                        args = self.parse_function_args(self.tokens[paren_pos:count_tokens - 1])
                        index = (last_token_start, args[1])

                        if not self.memory.get(index, False):
                            self.memory[index] = {}
                        if not self.memory.get(index, False).get("functions", False):
                            self.memory[index]["functions"] = {}
                        self.memory[index]["functions"][token_string] = {
                            "args": args[0]
                        }"""

            # detect call and create function
            if next_token_type == "OP":
                if next_token_string == "(":
                    if last_token_string == self.token_strings["function"]:
                        paren_pos = -1
                        for j in range(i, count_tokens):
                            if self.tokens[j]["name"] == "OP" and self.tokens[j]["string"] == "(":
                                paren_pos = j
                                break
                            
                        if paren_pos != -1:
                            args = self.parse_function_args(self.tokens[paren_pos:count_tokens - 1])
                            index = (last_token_start, args[1])

                            if not self.memory.get(index, False):
                                self.memory[index] = {}
                            if not self.memory.get(index, False).get("functions", False):
                                self.memory[index]["functions"] = {}
                            self.memory[index]["functions"][token_string] = {
                                "args": args[0]
                            }
                    else:
                        func_name = token_string
                        actual_func = self._resolve_variable_to_function(func_name)
                        paren_pos = i

                        args = self.parse_function_args(self.tokens[paren_pos:count_tokens - 1], True)
                        index = (last_token_start, token_end)

                        if not self.memory.get(index, False):
                            self.memory[index] = {}
                        if not self.memory[index].get("calls", False):
                            self.memory[index]["calls"] = {}

                        self.memory[index]["calls"][func_name] = {
                            "function": actual_func if actual_func else func_name,
                            "args": args[0],
                            "is_variable_call": True,
                            "resolved_from": func_name
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
                                paren_pos = -1
                                for j in range(i + 2, count_tokens):
                                    if self.tokens[j]["name"] == "OP" and self.tokens[j]["string"] == "(":
                                        paren_pos = j
                                        break
                                    
                                if paren_pos != -1:
                                    args = self.parse_function_args(self.tokens[paren_pos:count_tokens - 1], True)

                                    if not self.memory.get(index, False):
                                        self.memory[index] = {}
                                    if not self.memory[index].get("calls", False):
                                        self.memory[index]["calls"] = {}
                                    self.memory[index]["calls"][last_token_string] = {
                                        "function": next_token_string,
                                        "args": args[0]
                                    }
                            else:
                                # clone function
                                if not self.memory.get(index, False):
                                    self.memory[index] = {}
                                if not self.memory[index].get("assignments", False):
                                    self.memory[index]["assignments"] = {}
                                self.memory[index]["assignments"][last_token_string] = {
                                    "value" : next_token_string,
                                    "type" : "copy"
                                }

        print("blocks:")
        print(self.build_blocks())
        print(self.build_flow_graph())

    def _parse_single_arg(self, arg_str, is_call=False):
        arg_str = arg_str.strip()

        result = {
            "name" : arg_str,
            "type": None,
            "value": None
            }

        if is_call:
            parsed_value = self._parse_value(arg_str)
            arg_type = "literal"
            actual_type = type(parsed_value).__name__
            if isinstance(parsed_value, str) and not self._is_literal(arg_str):
                arg_type = "variable"

            result = {
                "value" : parsed_value,
                "type" : arg_type,
                "actual_type" : actual_type,
                "raw" : arg_str
            }
            return result

        if ":" in arg_str:
            name_part, rest = arg_str.split(":", 1)
            result["name"] = name_part.strip()

            if "=" in rest:
                type_part, value_part = rest.split("=", 1)
                if type_part.strip():
                    result["type"] = self._parse_value(type_part.strip())
                if value_part.strip():
                    result["value"] = self._parse_value(value_part.strip())
            else:
                if rest.strip():
                    result["type"] = self._parse_value(rest.strip())

        elif "=" in arg_str:
            name_part, value_part = arg_str.split("=", 1)
            result["name"] = name_part.strip()
            if value_part.strip():
                result["value"] = self._parse_value(value_part.strip())

        return result
    
    def _resolve_variable_to_function(self, var_name):
        for pos, data in self.memory.items():
            if "assignments" in data:
                for var, assign in data["assignments"].items():
                    if var == var_name:
                        value = assign["value"]
                        if self._is_function_name(value):
                            return value
                        else:
                            return self._resolve_variable_to_function(value)
        return var_name

    def _is_function_name(self, name):
        for pos, data in self.memory.items():
            if "functions" in data:
                if name in data["functions"]:
                    return True
        return False

    def _is_literal(self, arg_str):
        arg_str = arg_str.strip()

        if arg_str.isdigit():
            return True
        try:
            float(arg_str)
            return True
        except:
            pass
        
        if arg_str.lower() in ['true', 'false']:
            return True
        if arg_str.lower() == 'none':
            return True
        if (arg_str.startswith('"') and arg_str.endswith('"')) or (arg_str.startswith("'") and arg_str.endswith("'")):
            return True

        if arg_str.startswith(('[', '{', '(')) and arg_str.endswith((']', '}', ')')):
            return True
        return False
    
    def _parse_value(self, value_str):
        value_str = value_str.strip()

        if ":" in value_str and not value_str.startswith('"'):
            value_str = value_str.split(":")[0].strip()

        if not value_str:
            return None

        if value_str.startswith('{') and value_str.endswith('}'):
            return self._parse_dict(value_str)
        if value_str.startswith('[') and value_str.endswith(']'):
            return self._parse_list(value_str)
        if value_str.startswith('(') and value_str.endswith(')'):
            return self._parse_tuple(value_str)

        if value_str.isdigit():
            return int(value_str)
        try:
            if '.' in value_str:
                return float(value_str)
        except:
            pass
        
        if value_str.lower() == 'true':
            return True
        if value_str.lower() == 'false':
            return False

        if value_str.lower() == 'none':
            return None

        if (value_str.startswith('"') and value_str.endswith('"')) or (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]
        return value_str

    def _parse_list(self, list_str):
        content = list_str[1:-1].strip()
        if not content:
            return []

        items = []
        current = ""
        bracket_depth = 0
        quote_char = None

        for char in content:
            if char in "\"'":
                if quote_char is None:
                    quote_char = char
                elif quote_char == char:
                    quote_char = None

            if char == ',' and bracket_depth == 0 and quote_char is None:
                items.append(self._parse_value(current.strip()))
                current = ""
            else:
                current += char
                if char in "([{":
                    bracket_depth += 1
                elif char in ")]}":
                    bracket_depth -= 1

        if current.strip():
            items.append(self._parse_value(current.strip()))

        return items

    def _parse_dict(self, dict_str):
        content = dict_str[1:-1].strip()
        if not content:
            return {}

        result = {}
        current_key = None
        current_value = ""
        bracket_depth = 0
        quote_char = None
        in_key = True
        after_colon = False

        i = 0
        while i < len(content):
            char = content[i]

            if char in "\"'":
                if quote_char is None:
                    quote_char = char
                elif quote_char == char:
                    quote_char = None

            if char in "([{" and quote_char is None:
                bracket_depth += 1
            elif char in ")]}" and quote_char is None:
                bracket_depth -= 1

            if char == ':' and bracket_depth == 0 and quote_char is None and not after_colon:
                current_key = current_value.strip()
                current_value = ""
                after_colon = True
            elif char == ',' and bracket_depth == 0 and quote_char is None and after_colon:
                result[self._parse_value(current_key)] = self._parse_value(current_value.strip())
                current_key = None
                current_value = ""
                after_colon = False
            else:
                current_value += char

            i += 1

        if after_colon and current_key is not None:
            result[self._parse_value(current_key)] = self._parse_value(current_value.strip())

        return result

    def _parse_tuple(self, tuple_str):
        return tuple(self._parse_list(tuple_str))

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
