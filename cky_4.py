#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 14:05:50 2018

@author: s1856289
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 13:49:31 2018

@author: s1856289
"""

import sys,re
import nltk
from collections import defaultdict
import cfg_fix
from cfg_fix import parse_grammar, CFG
from pprint import pprint
# The printing and tracing functionality is in a separate file in order
#  to make this file easier to read
from cky_print import CKY_pprint, CKY_log, Cell__str__, Cell_str, Cell_log

class CKY:
    """An implementation of the Cocke-Kasami-Younger (bottom-up) CFG recogniser.

    Goes beyond strict CKY's insistance on Chomsky Normal Form.
    It allows arbitrary unary productions, not just NT->T
    ones, that is X -> Y with either Y -> A B or Y -> Z .
    It also allows mixed binary productions, that is NT -> NT T or -> T NT"""

    def __init__(self,grammar):
        '''Create an extended CKY processor for a particular grammar

        Grammar is an NLTK CFG
        consisting of unary and binary rules (no empty rules,
        no more than two symbols on the right-hand side

        (We use "symbol" throughout this code to refer to _either_ a string or
        an nltk.grammar.Nonterminal, that is, the two thinegs we find in
        nltk.grammar.Production)

        :type grammar: nltk.grammar.CFG, as fixed by cfg_fix
        :param grammar: A context-free grammar
        :return: none'''

        self.verbose=False
        assert(isinstance(grammar,CFG))
        self.grammar=grammar
        # split and index the grammar
        self.buildIndices(grammar.productions())

    def buildIndices(self,productions):
        '''
        Postcondition: Each right-hand side in the grammar is mapped to a list of its left-hand symbols using a dictionary
        How: Creates a dictionary for unary rules and a dictionary for binary rules
        If the right-hand side is in a unary rule, adds the single symbol as a key to unary dictionary; else adds a tuple of 2 right-hand side symbols as a key to binary dictionary
        For each left-hand symbol that expands to a right-hand side append that symbol to the right-hand side's list in the dictionary
        These dictionaries will later be used in CKY parsing to find all of the left-hand side symbols that can expand to the given right-hand side
        :type productions: nltk.grammar.Production
        :param productions: a list of rules in the grammar
        :return: none
        '''
        self.unary=defaultdict(list)
        self.binary=defaultdict(list)
        for production in productions:
            rhs=production.rhs()
            lhs=production.lhs()
            assert(len(rhs)>0 and len(rhs)<=2)
            if len(rhs)==1:
                self.unary[rhs[0]].append(lhs)
            else:
                self.binary[rhs].append(lhs)
    

    def recognise(self,tokens,verbose=False):
        '''replace/expand this docstring. Your docs need NOT
        say anything more about the verbose option.

        Initialise a matrix from the sentence,
        then run the CKY algorithm over it
        
        Postcondition: the CKY chart has been filled in and printed, a trace of the parse has been printed, the sentence has either been recognised or rejected by the grammar
        How: Create a matrix (a list to hold rows)
        Create rows (indexed beginning at 0)
        Create columns in each row (indexed beginning at 1)
        If the column index is greater than the row index, create a Cell at that index
        Add the row to the matrix
        Fill the Cells with the correct terminals and non-terminals by calling unaryFill and binaryFill

        :type tokens: list(str)
        :param tokens: a list of words in the sentence
        :type verbose: bool
        :param verbose: show debugging output if True, defaults to False
        :rtype: bool
        :return: true if the start symbol is in the index [0][n-1] in the chart (means the sentence was recognised); false otherwise

        '''
        self.verbose=verbose
        self.words = tokens
        self.n = len(self.words)+1
        self.matrix = []
        # We index by row, then column
        #  So Y below is 1,2 and Z is 0,3
        #    1   2   3  ...
        # 0  .   .   Z
        # 1      Y   .
        # 2          .
        # ...
        for r in range(self.n-1):
             # rows
             row=[]
             for c in range(self.n):
                 # columns
                 if c>r:
                     # This is one we care about, add a cell
                     row.append(Cell(r,c,self))
                 else:
                     # just a filler
                     row.append(None)
             self.matrix.append(row)
        self.unaryFill()
        self.binaryScan()
        # Replace the line below for Q6
        return self.grammar.start() in self.matrix[0][self.n-1].labels(), len(self.matrix[0][self.n-1].labels())

    def unaryFill(self):
        '''
        Postcondition: Each cell in the upper-left to bottom-right diagonal in column n is filled with the nth word in the token list and with any unary rules that expand to that word
        How: for each cell in the diagonal beginning in the upper-left cell, fill it with the rth word in the list.
        Call unaryUpdate to find the chain of unary rules that expand to that word and puts the LHS of those rules in the cell
        :return: none
        '''
        for r in range(self.n-1):
            cell=self.matrix[r][r+1]
            word=self.words[r]
            cell.addLabel(word)

    def binaryScan(self):
        '''(The heart of the implementation.)

        Postcondition: the matrix has been filled with all
        constituents that can be built from the input words and
        grammar.

        How: Starting with constituents of length 2 (because length 1
        has been done already), proceed across the upper-right
        diagonals from left to right and in increasing order of
        constituent length. Call maybeBuild for each possible choice
        of (start, mid, end) positions to try to build something at
        those positions.

        :return: none
        '''
        for span in range(2, self.n):
            for start in range(self.n-span):
                end = start + span
                for mid in range(start+1, end):
                    self.maybeBuild(start, mid, end)

    def maybeBuild(self, start, mid, end):
        '''
        Postcondition: the Cell at position [start][end] is filled with a Label for the LHS symbols that expands to the Labels in the Cell at position [start][mid] and the Cell at position [mid][end]
        Printed a list of all the binary rules in the Cell at position [start][end] in the order they were applied
        How: Gets the symbols in the Cell at position [start][mid] and the symbols in the Cell at position [mid][end]
        Creates a tuple for each combination of symbols in [start][mid] and symbols in [mid][end]
        Looks for each tuple in the binary dictionary and gets the list of LHS symbols that expand to the symbols in the tuple
        Adds each LHS symbol to the Cell at position [start][end]
        :type start: int
        :param start: the index for the row of the first symbol in the RHS and the row of the symbol in the LHS
        :type mid: int
        :param mid: the index for the column of the first symbol in the RHS and the row of the second symbol in the RHS
        :type end: int
        :param end: the index for the column of the symbol in the LHS
        :return: none
        '''
        self.log("%s--%s--%s:",start, mid, end)
        cell=self.matrix[start][end]
        for s1 in self.matrix[start][mid].labels():
            for s2 in self.matrix[mid][end].labels():
                if (s1,s2) in self.binary:
                    for s in self.binary[(s1,s2)]:
                        self.log("%s -> %s %s", s, s1, s2, indent=1)
                        cell.addLabel(s)

# helper methods from cky_print
CKY.pprint=CKY_pprint
CKY.log=CKY_log

class Cell:
    '''A cell in a CKY matrix'''
    def __init__(self,row,column,matrix):
        self._row=row
        self._column=column
        self.matrix=matrix
        self._labels=[]

    def addLabel(self,label):
        if label not in self._labels:
            self._labels.append(label)
            self.unaryUpdate(label)

    def labels(self):
        return self._labels

    def unaryUpdate(self,symbol,depth=0,recursive=False):
        '''add docstring here. You need NOT document the depth
        and recursive arguments, which are used only for tracing.
        Postcondition: printed a list of all the unary rules in a cell in the order they were applied in the CKY table.
        In the given cell, there are Labels for the word and the LHS NTs that expand to that word directly or through another unary rule
        How: for the given symbol, find its LHS in the unary dictionary (its parents), add a Label for each parent, call unaryUpdate recursively on each parent
        :type symbol: str
        :param symbol: a terminal or non-terminal that appears in the right-hand side of a production
        :return: none
        '''
        if not recursive:
            self.log(str(symbol),indent=depth)
        if symbol in self.matrix.unary:
            for parent in self.matrix.unary[symbol]:
                self.matrix.log("%s -> %s",parent,symbol,indent=depth+1)
                self.addLabel(parent)
                self.unaryUpdate(parent,depth+1,True)

# helper methods from cky_print
Cell.__str__=Cell__str__
Cell.str=Cell_str
Cell.log=Cell_log

class Label:
    '''A label for a substring in a CKY chart Cell

    Includes a terminal or non-terminal symbol, possibly other
    information.  Add more to this docstring when you start using this
    class'''
    def __init__(self,symbol,
                 # Fill in here, if more needed
                 ):
        '''Create a label from a symbol and ...
        :type symbol: a string (for terminals) or an nltk.grammar.Nonterminal
        :param symbol: a terminal or non-terminal
        :return: none
        '''
        self._symbol=symbol
        # augment as appropriate, with comments

    def __str__(self):
        return str(self._symbol)

    def __eq__(self,other):
        '''How to test for equality -- other must be a label,
        and symbols have to be equal
        :rtype: bool
        :return: True iff symbols are equal, else False
        '''
        assert isinstance(other,Label)
        return self._symbol==other._symbol

    def symbol(self):
        return self._symbol
    # Add more methods as required, with docstring and comments