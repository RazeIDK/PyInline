import os
import TokenMgr # tokens
import ControlFlowGraph # graphs

source = """

def agu(dad : False, kawda : str = 'dDsd'):
    print(123)

gg = agu
hh = gg
ll = hh
hh()

def aa(dg):
    print(dg)

aa("ggg")
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
