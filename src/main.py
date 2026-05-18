import ast
import copy
import os
import builtins
import time
import sys

source = r"""
# хэш пароля
hash_password = hash('PIZZA')

# функции
def check_password(input_data):
    if hash(input_data) == hash_password():
        return True
    else:
        return False

def main():
    password = input("Введите пароль: ")
    if check_password(password):
        print("Пароль верный!")
    else:
        print("Пароль неверный!")

if __name__ == "__main__":
    main()
"""

class InlineTransformer(ast.NodeTransformer):
    def __init__(self):
        self.funcs = {}
        self.temp_counter = 0
        self.builtin_functions = []

        for name in dir(builtins):
            obj = getattr(builtins, name)
            if isinstance(obj, (types.BuiltinFunctionType, types.FunctionType)):
                self.builtin_functions.append(name)

    def new_temp(self):
        self.temp_counter += 1
        return f"PyInline_{self.temp_counter}"

    def visit_FunctionDef(self, node):
        self.funcs[node.name] = node
        return None

    def inline_call(self, call_node):
        if not isinstance(call_node.func, ast.Name):
            return None, None
        name = call_node.func.id

        if name in self.builtin_functions:
            return None, None

        if name not in self.funcs:
            return None, ast.Name(id=name, ctx=ast.Load())

        func = self.funcs[name]

        if (len(func.body) == 1 and isinstance(func.body[0], ast.If) and len(func.body[0].body) == 1 and isinstance(func.body[0].body[0], ast.Return) and len(func.body[0].orelse) == 1 and isinstance(func.body[0].orelse[0], ast.Return)):

            ret_true = func.body[0].body[0].value
            ret_false = func.body[0].orelse[0].value
            if (isinstance(ret_true, ast.Constant) and ret_true.value is True and isinstance(ret_false, ast.Constant) and ret_false.value is False):
                
                
                arg_map = {arg.arg: call_node.args[i] for i, arg in enumerate(func.args.args)}
                
                class Replacer(ast.NodeTransformer):
                    def visit_Name(self, n):
                        if n.id in arg_map:
                            return copy.deepcopy(arg_map[n.id])
                        return n

                new_test = Replacer().visit(func.body[0].test)
                return None, new_test

        has_return = any(isinstance(stmt, ast.Return) for stmt in func.body)
        temp = self.new_temp() if has_return else None

        new_stmts = []
        for stmt in func.body:
            if isinstance(stmt, ast.Return):
                if temp:
                    new_stmts.append(
                        ast.Assign(
                            targets=[ast.Name(
                                id=temp, ctx=ast.Store()
                                )
                                ],
                            value=copy.deepcopy(stmt.value)
                            )
                        )
            else:
                new_stmts.append(copy.deepcopy(stmt))

        if has_return:
            return new_stmts, ast.Name(id=temp, ctx=ast.Load())
        else:
            return new_stmts, None
            
    def visit_Call(self, node):
        node.args = [self.visit(arg) for arg in node.args]
        body, repl = self.inline_call(node)

        if body is not None:
            processed_body = []
            for stmt in body:
                processed = self.visit(stmt)
                if isinstance(processed, list):
                    processed_body.extend(processed)
                elif processed is not None:
                    processed_body.append(processed)

            if repl is not None:
                repl = self.visit(repl)
                
                if isinstance(repl, list):
                    repl = repl[0] if len(repl) == 1 else repl

            if repl is None:
                return processed_body
            else:
                if not processed_body:
                    return repl
                return processed_body + [repl]
        else:
            if repl is not None:
                repl = self.visit(repl)
                if isinstance(repl, list):
                    repl = repl[0] if len(repl) == 1 else repl
                return repl
            return node

    def visit_Expr(self, node):
        val = self.visit(node.value)
        if isinstance(val, list):
            return val
        if val is None:
            return None
        node.value = val
        return node

    def visit_Assign(self, node):
        val = self.visit(node.value)
        if isinstance(val, list):
            return val[:-1] + [ast.Assign(targets=node.targets, value=val[-1])]
        node.value = val
        return node

    def visit_If(self, node):
        node.test = self.visit(node.test)
        node.body = self._flatten(node.body)
        node.orelse = self._flatten(node.orelse)
        return node

    def visit_Compare(self, node):
        node.left = self.visit(node.left)
        
        node.comparators = [self.visit(c) for c in node.comparators]
        return node

    def visit_BinOp(self, node):
        node.left = self.visit(node.left)
        node.right = self.visit(node.right)
        return node

    def _flatten(self, stmts):
        res = []
        for s in stmts:
            v = self.visit(s)
            if isinstance(v, list):
                res.extend(v)
            elif v is not None:
                res.append(v)
        return res

    def visit_Module(self, node):
        new_body = []
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef):
                self.visit(stmt)
            else:
                new_body.append(stmt)
        node.body = self._flatten(new_body)
        return node

def main():
    tree = ast.parse(source)
    print(ast.dump(tree, indent=2, include_attributes=False))
    print("=" * 20)

    transformer = InlineTransformer()
    transformed = transformer.visit(tree)

    if transformed is None:
        print("Сгенерированный код неккоректный")
        os._exit(0)

    ast.fix_missing_locations(transformed)
    try:
        code = ast.unparse(transformed)
    except Exception as err:
        print(err)
        print(ast.dump(transformed, indent=2))
        os_.exit(0)

    print("\nGenerated code")
    print(code)

    print("\nExecuting generated code")
    exec(code)

if __name__ == "__main__":
    main()