import flags, utils
from relations import *
from visitors import GatheringVisitor

class InferVisitor(GatheringVisitor):
    examine_functions = False
    def combine_expr(self, s1, s2):
        return s1 + s2
    combine_stmt = combine_expr
    combine_stmt_expr = combine_expr
    empty_stmt = list
    empty_expr = list
    def infer(self, typechecker, locals, ns, env, misc):
        lenv = {}
        env = env.copy()
        while True:
            assignments = super(InferVisitor, self).dispatch_statements(ns, env, misc, 
                                                                        typechecker)
            new_assignments = []
            while assignments:
                k, v = assignments[0]
                del assignments[0]
                if isinstance(k, ast.Name):
                    new_assignments.append((k,v))
                elif isinstance(k, ast.Tuple) or isinstance(k, ast.List):
                    if tyinstance(v, Tuple):
                        assignments += (list(zip(k.elts, v.elements)))
                    elif tyinstance(v, Iterable) or tyinstance(v, List):
                        assignments += ([(e, v.type) for e in k.elts])
                    elif tyinstance(v, Dict):
                        assignments += (list(zip(k.elts, v.keys)))
                    else: assignments += ([(e, Dyn) for e in k.elts])
            nlenv = {}
            print ([(k.id, v) for k,v in new_assignments])
            for local in locals:
                if not tyinstance(env[local], Bottom):
                    continue
                ltys = [y for x,y in new_assignments if x.id == local.var]
                ty = tyjoin(ltys)
                nlenv[local] = ty
            if nlenv == lenv:
                break
            else:
                env.update(nlenv)
                lenv = nlenv
        return env
    
    def visitAssign(self, n, env, misc, typechecker):
        _, vty = typechecker.dispatch(n.value, env, misc)
        assigns = []
        for target in n.targets:
            ntarget, _ = typechecker.dispatch(target, env, misc)
            if not (flags.SEMANTICS == 'MONO' and isinstance(target, ast.Attribute) and \
                        not tyinstance(tty, Dyn)):
                assigns.append((ntarget,vty))
        return assigns
    def visitAugAssign(self, n, env, misc, typechecker):
        optarget = utils.copy_assignee(n.target, ast.Load())

        assignment = ast.Assign(targets=[n.target], 
                                value=ast.BinOp(left=optarget,
                                                op=n.op,
                                                right=n.value),
                                lineno=n.lineno)
        return self.dispatch(assignment, env, misc, typechecker)
    def visitFor(self, n, env, misc, typechecker):
        target, _ = typechecker.dispatch(n.target, env, misc)
        _, ity = typechecker.dispatch(n.iter, env, misc)
        body = self.dispatch_statements(n.body, env, misc, typechecker)
        orelse = self.dispatch_statements(n.orelse, env, misc, typechecker)
        print ('rly', body)
        return [(target, utils.iter_type(ity))] + body + orelse
    
