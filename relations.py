from typing import * 
from tydecs import typed

def tyjoin(types):
    if len(types) == 0:
        return Dyn
    types = list(map(normalize, types))
    join = types[0]
    if tyinstance(join, Dyn):
        return Dyn
    for ty in types[1:]:
        if not tyinstance(ty, normalize(join).__class__) or \
                tyinstance(ty, Dyn):
            return Dyn
        elif tyinstance(ty, ClassStatic) or tyinstance(ty, InstanceStatic):
            join = join if ty.klass_name == join.klass_name else Dyn
        elif tyinstance(ty, List):
            join = List(tyjoin([ty.type, join.type]))
        elif tyinstance(ty, Tuple):
            if len(ty.elements) == len(join.elements):
                join = Tuple(*[tyjoin(list(p)) for p in zip(ty.elements, join.elements)])
            else: return Dyn
        elif tyinstance(ty, Dict):
            join = Dict(tyjoin([ty.keys, join.keys]), tyjoin([ty.values, join.values]))
        elif tyinstance(ty, Function):
            if len(ty.froms) == len(join.froms):
                join = Function([tyjoin(list(p)) for p in zip(ty.froms, join.froms)], 
                                tyjoin([ty.to, join.to]))
            else: return Dyn
        elif tyinstance(ty, Object):
            members = {}
            for x in ty.members:
                if x in join.members:
                    members[x] = tyjoin([ty.members[x], join.members[x]])
            join = Object(members)
        
        if join == Dyn: return Dyn
    return join

class Bot(Exception):
    pass

def tymeet(types):
    types = list(map(normalize, types))
    meet = types[0]
    for ty in types[1:]:
        if tyinstance(meet, Dyn):
            meet = ty
        elif tyinstance(ty, Dyn):
            continue
        elif not tyinstance(ty, normalize(meet).__class__):
            raise Bot()
        elif tyinstance(ty, List):
            join = List(tymeet([ty.type, meet.type]))
        elif tyinstance(ty, Tuple):
            if len(ty.elements) == len(join.elements):
                meet = Tuple(*[tymeet(list(p)) for p in zip(ty.elements, meet.elements)])
            else: raise Bot()
        elif tyinstance(ty, Dict):
            meet = Dict(tymeet([ty.keys, meet.keys]), tymeet([ty.values, meet.values]))
        elif tyinstance(ty, Function):
            if len(ty.froms) == len(meet.froms):
                meet = Function([tymeet(list(p)) for p in zip(ty.froms, meet.froms)], 
                                tymeet([ty.to, meet.to]))
            else: raise Bot()
        elif tyinstance(ty, Object):
            members = {}
            for x in ty.members:
                if x in join.members:
                    members[x] = tymeet([ty.members[x], meet.members[x]])
                else: members[x] = ty.members[x]
            for x in meet.members:
                if not x in members:
                    members[x] = meet.members[x]
            meet = Object(members)
    return meet

def prim_subtype(t1, t2):
    prims = [Bool, Int, Float, Complex]
    t1tys = [tyinstance(t1, ty) for ty in prims]
    t2tys = [tyinstance(t2, ty) for ty in prims]
    if not(any(t1tys)) or not(any(t2tys)):
        raise UnexpectedTypeError()
    return t1tys.index(True) <= t2tys.index(True)

def primjoin(tys, min=Int, max=Complex):
    try:
        ty = tys[0]
        for ity in tys[1:]:
            if prim_subtype(ty, ity):
                ty = ity
        if not prim_subtype(ty, max):
            return Dyn
        if prim_subtype(ty, min):
            return min
        else: return ty
    except UnexpectedTypeError:
        return Dyn
    except IndexError:
        return Dyn

def prim(ty):
    return any(tyinstance(ty, t) for t in [Bool, Int, Float, Complex])

def intlike(ty):
    return any(tyinstance(ty, t) for t in [Bool, Int])

def arith(op):
    return any(isinstance(op, o) for o in [ast.Add, ast.Mult, ast.Div, ast.FloorDiv, ast.Sub, ast.Pow, ast.Mod])

def shifting(op):
    return any(isinstance(op, o) for o in [ast.LShift, ast.RShift])

def logical(op):
    return any(isinstance(op, o) for o in [ast.BitOr, ast.BitAnd, ast.BitXor])

def listlike(ty):
    return any(tyinstance(ty, t) for t in [List, String, Tuple])

def table(l, r, op):
    if any(isinstance(op, o) for o in [ast.FloorDiv, ast.Mod]):
        if any(tyinstance(nd, ty) for nd in [l, r] for ty in [Complex, String, List, Tuple, Dict]):
            raise Bot
    if shifting(op) or logical(op):
        if any(tyinstance(nd, ty) for nd in [l, r] for ty in [Float, Complex, String, List, Tuple, Dict]):
            raise Bot
    if arith(op):
        if any(tyinstance(nd, ty) for nd in [l, r] for ty in [Dict]):
            raise Bot
        if not isinstance(op, Add) and not isinstance(op, Mult) and \
                any(tyinstance(nd, ty) for nd in [l, r] for ty in [String, List, Tuple]):
            raise Bot
    if any(tyinstance(nd, ty) for nd in [l, r] for ty in [Object, Dyn]):
        return Dyn
    if tyinstance(l, String):
        if tyinstance(r, String):
            if isinstance(op, ast.Add):
                return String
            else: raise Bot
        elif intlike(r): 
            if isinstance(op, ast.Mult):
                return String
            else: raise Bot
        else: raise Bot
    elif tyinstance(l, Bool):
        if arith(op) or shifting(op):
            if tyinstance(r, Bool):
                return Int
            elif prim(r):
                return r
            elif listlike(r) and isinstance(op, ast.Add):
                return r
            else: raise Bot
        elif logical(op):
            return r
        else:
            raise Bot
    #stopgap
    return Dyn
        
        
        