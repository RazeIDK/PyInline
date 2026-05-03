import os
import TokenMgr # tokens
import ControlFlowGraph # graphs

source = """
asd = 'gg'
fff = 239e
"""

def main():
    mgr = TokenMgr.Manager(source)

    print("tokens: ")
    mgr.print_tokens()

    print("map: ")
    cfg = ControlFlowGraph.Map(mgr._get_tokens())
    cfg.generate_map()
    cfg._get_debug()




if __name__ == "__main__":
    main()
