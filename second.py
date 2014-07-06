import jpype as java

import os
import shutil
from pprint import pprint

import re



analyzerActive = 0
pysonar = None
ast = None
types = None



CppKeywords = {}

INDENT = ' ' * 4




commonName = 'common.h'









def notSupported(msg):
    return '/* Warning: not supported: {} */'.format(msg)


class NameGenerator(object):
    def __init__(self, exclude):
        self.Exclude = exclude

        self.Chars = 'abcdefghijklmnopqrstuvwxyz'
        self.Counts = {}

    def gen(self, name='name'):
        c = self.Counts.get(name, 0)

        while True:
            r = '_{}_{}_'.format(name, self.buildID(c))
            if r in self.Exclude:
                c += 1
                continue
            break

        self.Counts[name] = c + 1
        return r

    def buildID(self, c):
        r = ''
        l = len(self.Chars)
        while True:
            r += self.Chars[c % l]
            c /= l
            if not c:
                break
        return r



class Type(object):
    def __init__(self, name):
        self.Name = name

    def typeInit(self):
        return []

    def varInit(self, name):
        return '{} {}'.format(self.strType(), name)

    def strType(self):
        return self.Name

    def __hash__(self):
        return hash(self.Name)

    def __eq__(self, other):
        if type(self) != type(other):
            return False

        return self.Name == other.Name

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return self.Name
    __repr__ = __str__

class PrimitiveType(Type):
    Names = {}

    def __init__(self, typ):
        Type.__init__(self, PrimitiveType.Names[type(typ)])


class SeqType(object):
    def len(self):
        raise NotImplementedError

    def strItem(self, i):
        raise NotImplementedError

    def itemType(self, i):
        raise NotImplementedError

    def slice(self, name, slice, typ):
        raise NotImplementedError

    def _parseSlice(self, slice, n):
        start = slice.start
        if start == None:
            start = 0
        elif start < 0:
            start += n
        if start < 0 or n <= start:
            return None

        stop = slice.stop
        if stop == None:
            stop = n
        elif stop < 0:
            stop += n
        elif n < stop:
            stop = n
        if stop <= start: # or stop < 0
            return None

        step = slice.step
        if step == None:
            step = 1
        elif step == 0:
            raise ValueError('slice step cannot be zero')

        return start, stop, step


class ArrayType(Type, SeqType):
    def __init__(self, eltType, n):
        Type.__init__(self, 'anonymous')
        SeqType.__init__(self)

        self.ElementType = eltType
        self.N = n

    def strType(self):
        return 'array<{}, {}>'.format(self.ElementType.strType(), self.N)

    def len(self):
        return self.N

    def strItem(self, i):
        return '[{}]'.format(i)

    def itemType(self, i):
        return self.ElementType

    def __hash__(self):
        return hash((ArrayType, self.ElementType, self.N))

    def __eq__(self, other):
        if type(other) != ArrayType:
            return False

        return self.ElementType == other.ElementType and self.N == other.N

    def slice(self, name, slice, typ):
        items = self._parseSlice(slice, self.N)
        if items == None:
            return '({}){{}}'.format(typ.strType())

        start, stop, step = items

        if step != 1:
            return self._sliceExt(start, stop, step)

        return '{}.slice<{}>({})'.format(name,
                                         stop - start,
                                         start)

    def _sliceExt(self, start, stop, step):
        raise NotImplementedError


class StructType(Type, SeqType):
    def __init__(self, eltTypes):
        Type.__init__(self, None)
        SeqType.__init__(self)

        self.ElementTypes = tuple(eltTypes)

    def typeInit(self):
        r = ['struct %s {' % self.Name]
        r.extend('    {};'.format(eltType.varInit('_{}'.format(i)))
                                  for i, eltType in enumerate(self.ElementTypes))
        r.append('};')
        return r

    def len(self):
        return len(self.ElementTypes)

    def strItem(self, i):
        return '._{}'.format(i)

    def itemType(self, i):
        return self.ElementTypes[i]

    def __hash__(self):
        return hash((StructType, self.ElementTypes))

    def __eq__(self, other):
        if type(other) != StructType:
            return False

        return self.ElementTypes == other.ElementTypes

    def slice(self, name, slice, typ):
        items = self._parseSlice(slice)

        if items == None:
            return '({}){{}}'.format(typ.strType())

        start, stop, step = items

        return '({}){{}}'.format(typ.strType(),
                                 ', '.join(name + self.strItem(i)
                                           for i in xrange(start, stop, step)))




class ListType(Type, SeqType):
    def __init__(self, eltType):
        Type.__init__(self, 'anonymous')
        SeqType.__init__(self)

        self.ElementType = eltType

    def strType(self):
        s = self.ElementType.strType()
        return 'std::vector<{}{}>'.format(s, ' ' if s[-1] == '>' else '')

    def strItem(self, i):
        return '[{}]'.format(i)

    def itemType(self, i):
        return self.ElementType

    def __hash__(self):
        return hash(('List', self.ElementType))

    def __eq__(self, other):
        if type(other) != ListType:
            return False

        return self.ElementType == other.ElementType

    def asArrayType(self, n):
        return ArrayType(self.ElementType, n)


class InstanceType(Type):
    # TODO
    def __init__(self, name):
        Type.__init__(self, name)

class FunctionType(Type):
    def __init__(self, typ, argTypes, returnType):
        Type.__init__(self, None)

        self.Typ = typ
        self.ArgTypes = argTypes
        self.ReturnType = returnType

        self.Args = None # [str]
        self.Defaults = None # {arg: str}
        ##self.StarArg = None # str
        ##self.StarArgType = None
        ##self.KwArg = None # str
        ##self.KwArgType = None

    def typeInit(self):
        ##argTypes = self.ArgTypes[::]
        ##if self.StarArg != None:
            ##argTypes.append(self.StarArgType)
        ##if self.KwArg != None:
            ##argTypes.append(self.KwArgType)
        argTypes = self.ArgTypes

        return ['typedef {} (&{})({});'.format(self.ReturnType.strType(),
                                               self.Name,
                                               ', '.join(t.strType() for t in argTypes))]

    def strHead(self, name):
        ##args = self.Args[::]
        ##argTypes = self.ArgTypes[::]
        ##if self.StarArg != None:
            ##args.append(self.StarArg)
            ##argTypes.append(self.StarArgType)
        ##if self.KwArg != None:
            ##args.append(self.KwArg)
            ##argTypes.append(self.KwArgType)
        args = self.Args
        argTypes = self.ArgTypes

        return '{} {}({})'.format(self.ReturnType.strType(),
                                  name,
                                  ', '.join(t.varInit(arg) for t, arg in zip(argTypes, args)))

    def strCall(self, name, args, keywords): ##, starargs, kwargs):
        r = []
        r.extend(args)

        args = self.Args[len(args)::]

        for arg in args:
            v = keywords.get(arg, None)
            if v == None:
                v = self.Defaults.get(arg, None)
                if v == None:
                    raise NotImplementedError

            r.append(v)

        ##if self.StarArg != None:
            ##if starargs == None:
                ##starargs = 'NULL'
            ##r.append(starargs)

        ##if self.KwArg != None:
            ##if kwargs == None:
                ##kwargs = 'NULL'
            ##r.append(kwargs)

        return '{}({})'.format(name, ', '.join(r))

    def __hash__(self):
        return hash(self.Typ)

    def __eq__(self, other):
        if type(self) != type(other):
            return False

        return self.Typ == other.Typ


class LineTree(object):
    def __init__(self, level=0, parent=None):
        self.Level = level
        self.Parent = parent

        self.Indent = INDENT * level
        self.Items = []

    def append(self, line):
        self.Items.append(line)

    def extend(self, lines):
        self.Items.extend(lines)

    def createNode(self):
        r = LineTree(self.Level, self.Parent)
        self.Items.append(r)
        return r

    def createLevel(self):
        r = LineTree(self.Level + 1, self)
        self.Items.append(r)
        return r

    def leaveLevel(self):
        return self.Parent

    def remove(self, item):
        self.Items.remove(item)

    def pop(self):
        return self.Items.pop()

    def __str__(self):
        return '\n'.join((self.Indent + item) if type(item) == str else str(item)
                         for item in self.Items)


'''
    Variable Scope

python:
    search order:
        - local namespace
        - parent functions' namespace
        - global namespace (module)
        - builtins

C++:
    search order:
        - local namespace
        - global namespace (file)

solution:
    - parent functions' variables are brought into local scope via additional argument if necessary
    -- Attention: avoid name conflict
    -- the functions arguments are known when the entire function was parsed
    - builtins are converted into C++ equivalents where possible
    - module level = C++ main function level
    --? instead of passing variables from main function to called functions their declaration is moved to global scope

decision:
    - global C++ namespace is used for:
        - base implementation like array type, range, ...
        - anonymous types like structs
        - functions' default arguments
        - truely global python variables
        -- artificially (global keyword)
           or naturally


    Functions

python:
    - functions may be nested
    - may have complex default parameters

C++:
    - functions are declared inside a class, namespace or global but nowhere else
    - default parameters of C++ functions are of limited use

solution:
    - move nested functions to next class or namespace
    - declare variables for default arguments in next class or namespace
      initialize these variables where the python function is defined
    -- restore default argument variables before leaving scope to allow recursive function definitions
'''



def ensureDir(path):
    if os.path.exists(path):
        return

    os.makedirs(path)


class Py2Cpp(object):
    def __init__(self, inc='./inc', src='./src'):
        self.Inc = inc
        self.Src = src

        global analyzerActive
        global pysonar, ast, types

        if analyzerActive == 0:
            print '>', 'prepare type inference'
            java.startJVM(java.getDefaultJVMPath(), '-Djava.class.path=pysonar')

            pysonar = java.JPackage('org.yinwang.pysonar')
            ast = pysonar.ast
            types = pysonar.types

            self.onJVMboot()

        self.Analyzer = pysonar.Analyzer()
        analyzerActive += 1

        self.Bindings = None # qname: binding


        self.LineTrees = []

        # LineTrees
        self.Header = None
        self.HeaderHead = None
        self.Cpp = None
        self.CppHead = None
        self.Hidden = None

        self.VarDefinition = None
        self.FunDefinition = None
        self.EndOfScope = None

        self.NameGen = None
        self.BindName = None
        self.Names = set()
        self.Types = {}
        self.Functions = {}


    def close():
        if self.Analyzer == None:
            return

        self.Analyzer.close()

        global analyzerActive
        analyzerActive -= 1

        if analyzerActive == 0:
            java.shutdownJVM()

            self.onJVMshutdown()


    def parse(self, path):
        path = os.path.abspath(path)

        print '>', 'perform type inference with pysonar ..'

        analyzer = self.Analyzer
        analyzer.analyze(path)
        analyzer.finish()

        self.checkSonarErrors()

        self.Bindings = {binding.qname: binding for binding in analyzer.getAllBindings()}

        for file in analyzer.loadedFiles:
            file = str(file)
            print '>', 'parse file "{}"'.format(file)
            self.parseFile(file)


    def checkSonarErrors(self):
        analyzer = self.Analyzer

        if len(analyzer.failedToParse) != 0:
            print
            for path in analyzer.failedToParse:
                print 'pysonar: failed to parse "{}"'.format(path)

        if len(analyzer.semanticErrors) != 0:
            print
            for path in analyzer.semanticErrors:
                print 'pysonar: semantic errors in "{}"'.format(path)
                for diagnostic in analyzer.semanticErrors[path]:
                    print diagnostic.category, '"{}"'.format(diagnostic.msg)


    NodeParser = {}

    def onJVMboot(self):
        nodeParser = Py2Cpp.NodeParser
        nodeParser[ast.Import] = Py2Cpp.parseImport
        nodeParser[ast.Assign] = Py2Cpp.parseAssign
        nodeParser[ast.Tuple] = Py2Cpp.parseTuple
        nodeParser[ast.PyList] = Py2Cpp.parseList
        nodeParser[ast.PyInt] = Py2Cpp.parseInt
        nodeParser[ast.Name] = Py2Cpp.parseName
        nodeParser[ast.FunctionDef] = Py2Cpp.parseFunctionDef
        nodeParser[ast.Expr] = Py2Cpp.parseExpr
        nodeParser[ast.Call] = Py2Cpp.parseCall
        nodeParser[ast.Return] = Py2Cpp.parseReturn
        nodeParser[ast.Str] = Py2Cpp.parseStr

        primTypes = Py2Cpp.PrimitiveTypes
        primTypes.add(types.IntType)
        primTypes.add(types.FloatType)
        primTypes.add(types.StrType)

        primNames = PrimitiveType.Names
        primNames[types.IntType] = 'int'
        primNames[types.FloatType] = 'double'
        primNames[types.StrType] = 'std::string'

        complexTypes = Py2Cpp.ComplexTypes
        complexTypes[types.TupleType] = Py2Cpp._parseTupleType
        complexTypes[types.ListType] = Py2Cpp._parseListType
        complexTypes[types.FunType] = Py2Cpp._parseFunType
        complexTypes[types.InstanceType] = Py2Cpp._parseInstanceType


    def onJVMshutdown(self):
        Py2Cpp.NodeParser.clear()

        Py2Cpp.PrimitiveTypes.clear()
        PrimitiveType.Names.clear()

        Py2Cpp.ComplexTypes.clear()



    def parseFile(self, path):
        name, bindName = self.namesFromPath(path)
        hName = name + '.h'
        hiddenName = name + '.hidden'

        self.Header = header = LineTree()
        self.Cpp = cpp = LineTree()
        self.Hidden = hidden = LineTree()

        self.HeaderHead = headerHead = header.createNode()
        headerHead.append('#pragma once')
        headerHead.append('#include "{}"'.format(commonName))
        headerHead.append('#include "{}"'.format(hiddenName))

        header.append('namespace %s {' % (name,))
        header = header.createLevel()
        header.append('int main(std::string __name__);')

        self.CppHead = cppHead = cpp.createNode()
        cppHead.append('#include "{}"'.format(hName))

        cpp.append('namespace %s {' % (name,))
        cpp = cpp.createLevel()

        varDefinition = cpp.createNode()
        funDefinition = cpp.createNode()

        cpp.append('int main(std::string __name__) {')
        cpp = cpp.createLevel()

        hidden.append('#include "{}"'.format(commonName))
        hidden.append('namespace %s {' % (name,))
        hidden = hidden.createLevel()

        self.Header = header
        self.Cpp = cpp
        self.Hidden = hidden

        self.VarDefinition = varDefinition
        self.FunDefinition = funDefinition
        self.EndOfScope = cpp.createNode()
        cpp.pop()

        self.NameGen = NameGenerator([]) # TODO exclude local names
        self.BindName = bindName
        self.Types.clear()
        self.Names.clear()

        module = self.Analyzer.getAstForFile(path)
        self.parseBlock(module.body)

        cpp.append(self.EndOfScope)
        cpp.append('return 0;')

        cpp = cpp.leaveLevel() # leave main
        cpp.append('}')

        cpp = cpp.leaveLevel() # leave namespace
        cpp.append('}')

        header = header.leaveLevel() # leave namespace
        header.append('}')

        hidden = hidden.leaveLevel() # leave namespace
        hidden.append('}')

        self.Header = header
        self.Cpp = cpp
        self.Hidden = hidden

        # TODO main
        if name == 'target':
            cpp.append('int main(int argc, char const* argv[]) {')
            cpp.createLevel().append('return {}::main("__main__");'.format(name))
            cpp.append('}')


        ensureDir(self.Inc)

        _path = os.path
        with open(_path.join(self.Inc, hName), 'wb') as f:
            f.write(str(header))

        with open(_path.join(self.Inc, hiddenName), 'wb') as f:
            f.write(str(self.Hidden))

        base, t = os.path.split(__file__)
        commonSource = os.path.join(base, commonName)
        commonTarget = os.path.join(self.Inc, commonName)

        # TODO copy common.h

        ensureDir(self.Src)

        with open(_path.join(self.Src, name + '.cpp'), 'wb') as f:
            f.write(str(cpp))

    def namesFromPath(self, path):
        _path = os.path
        base, name = _path.split(path)

        if name == '__init__.py':
            names = []
        else:
            name, t = _path.splitext(name)
            names = [name]

        while True:
            if not _path.exists(_path.join(base, '__init__.py')):
                break

            base, name = _path.split(base)
            names.append(name)

        names.reverse()
        name = '_'.join(names)

        bindName = '{}.{}.'.format(base.replace('/', '.'),
                                  '.'.join(names))

        return name, bindName



    def parseNode(self, node):
        return Py2Cpp.NodeParser.get(type(node), Py2Cpp.parseUnkown)(self, node)

    def parseUnkown(self, node):
        self.Cpp.append('/* Unkown Node: {}, {} */'.format(type(node), node))


    def parseBlock(self, node):
        if node == None:
            return False

        for node in node.seq:
            self.parseNode(node)

        return type(node) == ast.Return


    def parseImport(self, node):
        for alias in node.names:
            name = '_'.join(name.id for name in alias.name)
            self.HeaderHead.append('#include "{}.h"'.format(name))

            self.Cpp.append('{}::main("{}");'.format(name, name))

            if alias.asname == None:
                continue

            self.Cpp.append('#define {} {}'.format(name, alias.asname.id))
            node = self.Cpp.createNode()
            self.Cpp.append('#undef {}'.format(alias.asname.id))
            self.Cpp = node


    def parseAssign(self, node):
        return self._parseAssign(node.target, self.parseNode(node.value), self.parseTypeOf(node.value))

    def _parseAssign(self, target, valueStr, typ):
        if type(target) == ast.Name:
            self.__parseAssign(self.parseName(target), valueStr, typ=typ)
            return

        var = self.NameGen.gen('var')
        self.__parseAssign(var, valueStr, typ=typ)

        for i, element in enumerate(target.elts):
            self._parseAssign(element, var + typ.strItem(i), typ.itemType(i))

    def __parseAssign(self, name, valueStr, typ=None, defi=None):
        if name in self.Names: # already defined
            self.Cpp.append(
                '{} = {};'.format(name, valueStr)
            )
            return
        self.Names.add(name)

        if defi == None:
            defi = self.VarDefinition

        if defi == None: # no definition area
            self.Cpp.append(
                '{} = {};'.format(typ.varInit(name), valueStr)
            )
            return

        varInit = typ.varInit(name)
        defi.append('{};'.format(varInit))
        self.Header.append('extern {};'.format(varInit))
        self.Cpp.append(
            '{} = {};'.format(name, valueStr)
        )

    def createAssign(self, targetStr, valueStr):
        return '{} = {};'.format(targetStr, valueStr)


    def parseTypeOf(self, node):
        if type(node) == ast.Name:
            qname = self.BindName + node.id
            binding = self.Bindings.get(qname, None)

            if binding == None:
                qname = '__builtin__.' + node.id
                binding = self.Bindings[qname]

            return self._parseType(binding.type)

        return self._parseType(node.transType)

    PrimitiveTypes = set()
    ComplexTypes = {}

    def _parseType(self, typ):
        typetype = type(typ)
        if typetype in Py2Cpp.PrimitiveTypes:
            t = PrimitiveType(typ)
        else:
            t = Py2Cpp.ComplexTypes[typetype](self, typ)

        r = self.Types.get(t, None)
        if r == None:
            self.Types[t] = t

            if t.Name == None:
                t.Name = self.NameGen.gen('type')
                self.Hidden.extend( t.typeInit() )

            r = t

        return r

    def _parseTupleType(self, typ):
        eltTypes = [self._parseType(eltType)
                    for eltType in typ.eltTypes]

        iTypes = iter(eltTypes)
        first = next(iTypes)
        for eltType in iTypes:
            if eltType != first:
                return StructType(eltTypes)

        return ArrayType(first, len(eltTypes))

    def _parseListType(self, typ):
        return ListType(self._parseType(typ.eltType))

    def _parseFunType(self, typ):
        if 1 < len(typ.arrows):
            raise Exception() # TODO

        args, = typ.arrows
        returns = typ.arrows[args]

        argTypes = [self._parseType(t) for t in args.eltTypes]
        returnType = self._parseType(returns)

        return FunctionType(typ, argTypes, returnType)

    def _parseInstanceType(self, typ):
        # TODO
        if typ.classType.name == '?':
            return InstanceType('void*')
        raise NotImplementedError


    def parseTuple(self, node, typ=None):
        r = ', '.join(self.parseNode(element) for element in node.elts)
        r, t = re.subn(r'\(.+?\)\{', ' ', r)
        r = r.replace('}', ' ')
        if typ == None:
            typ = self.parseTypeOf(node)
        return '({}){{{}}}'.format(typ.strType(), r)

    def parseList(self, node):
        typ = self.parseTypeOf(node)

        var = self.NameGen.gen('var')
        arrayType = typ.asArrayType(len(node.elts))
        self.__parseAssign(var,
                           self.parseTuple(node, arrayType),
                           typ=arrayType)

        return '{}({}.begin(), {}.end())'.format(typ.strType(), var, var)

    def parseInt(self, node):
        return str(node.value)

    def parseExpr(self, node):
        self.Cpp.append(
            '{};'.format(self.parseNode(node.value))
        )

    def parseReturn(self, node):
        var = self.NameGen.gen('return')
        self.__parseAssign(var, self.parseNode(node.value), self.parseTypeOf(node.value))

        self.Cpp.append(
            'return {};'.format(var)
        )

    def parseStr(self, node):
        return '"{}"'.format(node.value)


    def parseName(self, node):
        return self._parseName(node.id)

    def _parseName(self, name):
        # TODO exclude
        #if name in CppKeywords:
            #return name + '_';
        return name


    def parseFunctionDef(self, node):
        name = node.name.id
        funType = self.parseTypeOf(node.name)


        # parse args, defaults
        args = [n.id for n in node.args]
        funType.Args = args

        defaults = {}
        defBackups = {}
        for arg, nod in zip(reversed(args), reversed(node.defaults)):
            nam = '_{}_{}_'.format(name, arg)
            typ = self.parseTypeOf(nod)

            defBackup = self.NameGen.gen('default')
            defBackups[nam] = defBackup

            self.__parseAssign(defBackup, nam, typ=typ) # create default backup
            self.__parseAssign(nam, self.parseNode(nod), typ=typ, defi=self.FunDefinition)

            defaults[arg] = nam

        funType.Defaults = defaults


        ##stararg = node.vararg
        ##if stararg == None:
            ##starargType = None
        ##else:
            ##starargType = self.parseTypeOf(stararg)
            ##stararg = stararg.id

        ##funType.StarArg = stararg
        ##funType.StarArgType = starargType


        ##kwarg = node.kwarg
        ##if kwarg == None:
            ##kwArgType = None
        ##else:
            ##kwargType = self.parseTypeOf(kwarg)
            ##kwarg = kwarg.id

        ##funType.KwArg = kwarg
        ##funType.KwArgType = kwargType

        bindName = self.BindName
        self.BindName += name + '.'
        varDefinition = self.VarDefinition
        self.VarDefinition = None
        endOfScope = self.EndOfScope
        self.EndOfScope = self.Cpp.createNode()
        self.Cpp.pop()

        header = self.Header.createNode() # create function declaration node
        funDefiniton = self.FunDefinition.createNode()
        defHead = funDefiniton.createNode() # create function head node

        cpp = self.Cpp
        self.Cpp = funDefiniton.createLevel() # switch to function definition


        returns = self.parseBlock(node.body)
        returns = self.Cpp.pop() if returns else None

        self.Cpp.append(self.EndOfScope)

        self.Cpp.append('return NULL;' if returns == None else returns)
        funDefiniton.append('}')


        self.BindName = bindName
        self.VarDefinition = varDefinition
        self.EndOfScope = endOfScope


        self.Cpp = endOfScope

        for nam, defBackup in defBackups.iteritems():
            self.__parseAssign(nam, defBackup)

        self.Cpp = cpp


        if node.vararg != None:
            msg = notSupported('variable arguments')
            header.append(msg)
            defHead.append(msg)

        if node.kwarg != None:
            msg = notSupported('variable keyword arguments')
            header.append(msg)
            defHead.append(msg)


        head = funType.strHead(name)
        header.append('{};'.format(head))
        defHead.append('%s {' % (head,))


    def parseCall(self, node):
        name = node.func.id
        funType = self.parseTypeOf(node.func)

        args = [self.parseNode(a) for a in node.args]
        keywords = {kw.arg: self.parseNode(kw.value) for kw in node.keywords}

        starargs = node.starargs
        if starargs != None:
            starargsType = self.parseTypeOf(starargs)
            starargs = self.parseNode(starargs)


        ##kwargs = node.kwargs
        ##if kwargs != None:
            ##kwargs = self.parseNode(kwargs)


        d = len(funType.Args) - len(args)
        if d: # not all arguments have a value
            if starargs != None: # consume values from *args
                var = self.NameGen.gen('var')
                self.__parseAssign(var, starargs, typ=starargsType)

                d = min(d, starargsType.len())
                for i in xrange(d):
                    args.append(var + starargsType.strItem(i))

                if d < starargsType.len(): # *args is not entirely consumed
                    self.Cpp.append(notSupported('variable arguments'))


                ##var = self.NameGen.gen('var')
                ##self.__parseAssign(var,
                                   ##starargsType.slice(var, slice(d, None, None), funType.StarArgType),
                                   ##typ=funType.StarArgType)

                ##starargs = var


        ##d = len(funType.Args) - len(args)

        if node.kwargs != None:
            self.Cpp.append(notSupported('variable keyword arguments'))


        return funType.strCall(name, args, keywords)




    #def getNameType(self, name):
        #fullName = '{}.{}'.format(self.BaseName, name)
        #return self.BindTypes[fullName].type

    #OpStr = {
    #}

    #def parseBinOp(self, node):
        #left = self.parseNode(node.left)
        #right = self.parseNode(node.right)
        #op = Py2Cpp.OpStr[node.op]
        #return '({} {} {})'.format(left, op, right)

    #def parseFor(self, node):
        #init, begin, end = self.createForType(node.target, node.iter)

        #self.Writer.extend(init)
        #self.Writer.append('while( true ) {')

        #self.Writer.incLevel()
        #self.Writer.extend(begin)

        #self.parseNode(node.body)

        #self.Writer.extend(end)
        #self.Writer.decLevel()

        #self.Writer.append('}')

        #return ''


    #CreateFors = {}

    #def createForType(self, target, iter):
        #return Py2Cpp.CreateFors[type(iter.transType)](self, target, iter)

    #def createForTuple(self, target, iter):
        #tuple = self.parseNode(iter)
        #var = next(self.VarNameGen)
        #i = next(self.INameGen)

        #init = [self.createAssign(var, tuple, typ=strType(iter.transType)),
                #self.createAssign(i, '0', typ='int'),
                #self.createAssign(target, None)]
        #begin = ['if( {} == {} ) break;'.format(i, len(iter.elts)),
                 #'{} = {}[{}];'.format(self.parseNode(target), var, i)]
        #end = ['{}++;'.format(i)]
        #return init, begin, end




    #def parseClassDef(self, node):
        #name = self.parseNode(node.name)
        #self.Writer.append('class %s%s {' % (name, ' : {}'.format(', '.join(self.parseNode(base)
                                                                            #for base in node.bases))
                                                    #if len(node.bases) else ''))

        #self.Writer.incLevel()
        #self.ClassName = name

        #self.parseNode(node.body)

        #self.Writer.decLevel()

        #self.Writer.append('}')
        #return ''

    #def parsePass(self, node):
        #return ''

    #def parseFunctionDef(self, node):
        #if node.isLamba:
            #raise NotImplementedError

        #typStr = strType(node.transType)
        #name = self.parseNode(node.name)
        #self.Writer.append('%s %s(void) {' % (strType(node.transType),
                                              #'{}::{}'.format(self.ClassName, name)
                                                              #if len(self.ClassName) else name))

        #self.Writer.incLevel()

        #self.parseNode(node.body)

        #self.Writer.decLevel()

        #self.Writer.append('}')
        #return ''

    #def parseCall(self, node):
        #func = self.parseNode(node.func)
        #return '{}()'.format(func)

    #def parseExpr(self, node):
        #return '{};'.format( self.parseNode(node.value) )

    #def parseAttribute(self, node):
        #return '{}.{}'.format(self.parseNode(node.target), self.parseNode(node.attr))

    #def parsePrint(self, node):
        #return 'std::cout << {} << "\\n";'.format(' << '.join(self.parseNode(value)
                                                     #for value in node.values))

    #def parseBreak(self, node):
        #return 'break;'




py2Cpp = Py2Cpp(inc='.', src='.')
py2Cpp.parse('target.py')








