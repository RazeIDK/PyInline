import os
import ast

source = """
ff = True
def aa(gg : bool):
    if ff != False:
        print(gg)
aa(ff)
"""

class VisitorInline(ast.NodeTransformer):
    def __init__(self):
        self.memory_functions = {}

    def visit_FunctionDef(self, node):
        self.memory_functions[node] = None
        print(node)

        return None
    
    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            function_name = node.value.func.id
            value = None
            
            for i in range(len(self.memory_functions.keys())):
                mem = list(self.memory_functions.keys())[i]

                if function_name == mem.name:
                    assigns = []
                    for arg in mem.args.args:
                        annotation = arg.annotation.id
                        arg_var = arg.arg

                        arg_call = node.value.args[i]

                        assigns.append(
                            ast.Assign(
                                targets=[
                                    ast.Name(id=arg_var, ctx=ast.Store())
                                    ],
                                value=arg_call, kind=None)
                        )

                        assigns.append(
                            ast.If(
                                test=ast.UnaryOp(
                                    op=ast.Not(),
                                    operand=ast.Call(
                                        func=ast.Name(id='isinstance', ctx=ast.Load()),
                                        args=[
                                            ast.Name(id=arg_var, ctx=ast.Load()),
                                            ast.Name(id=annotation, ctx=ast.Load())])),
                                body=[
                                    ast.Raise(
                                        exc=ast.Call(
                                            func=ast.Name(id='ValueError', ctx=ast.Load())
                                        )
                                    )
                                ]
                            )
                        )
                    
                    mem.body = assigns + mem.body
                    return mem.body
                    break

        return node


def main():
    tree = ast.parse(source)
    print(ast.dump(tree, indent=4, include_attributes=False))
    print("="*20 + "\n")
    transformed = VisitorInline().visit(tree)
    ast.fix_missing_locations(transformed)

    print("\n" + "="*20)
    print(ast.unparse(transformed))

    print("\n" + "="*20)
    exec(ast.unparse(transformed))


if __name__ == "__main__":
    main()