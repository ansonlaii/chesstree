"""
=== Module Description ===
This module contains the basic tree interface required by the treemap
visualiser.
"""
from __future__ import annotations
import os
import math
from random import randint
from typing import Optional
import webbrowser
import json

class OperationNotSupportedError(Exception):
    """
    Error to indicate that a given operation is not supported.
    """

########
# Functions
########
def example_tree() -> TMTree:
    """
    example TMTree
    """
    j = TMTree('j', [], 10)
    k = TMTree('k', [], 5)
    e = TMTree('e', [j, k], 5)
    f = TMTree('f', [], 5)
    b = TMTree('b', [e, f], 5)
    g = TMTree('g', [], 4)
    h = TMTree('h', [], 4)
    i = TMTree('i', [], 2)
    c = TMTree('c', [g, h, i], 5)
    d = TMTree('d', [], 10)
    a = TMTree('a', [b, c, d], 5)
    a.update_rectangles((0, 0, 55, 30))
    return a


def path_to_nested_tuple(path: str) -> tuple[str, int | list]:
    """
    Return a nested tuple representing the files and directories rooted at path.

    A file is represented by a tuple consisting of its name and its size.

    A directory is represented by a tuple consisting of its name, and a list
    of tuples representing the files and subdirectories that it contains.

    The size of a file is defined to be 1 + the size of the file as reported by
    the os.path.getsize function.

    Precondition:
    <path> is a valid path to a FILE or a DIRECTORY.

    >>> path = os.path.join("example-directory", "workshop", "prep")
    >>> rslt = path_to_nested_tuple(path)
    >>> rslt[0]
    'prep'
    >>> rslt[1]
    [('images', [('Cats.pdf', 17)]), ('reading.md', 7)]
    """
    name = os.path.basename(path)
    if not os.path.isdir(path):
        return name, os.path.getsize(path) + 1
    else:
        files = []
        for filename in ordered_listdir(path):
            path2 = os.path.join(path, filename)
            files.append(path_to_nested_tuple(path2))
        return name, files


def ordered_listdir(path: str) -> list[str]:
    """
    Return a list of the files and directories of the given <path>.

    Hidden files that start with "." are ignored and
    the returned strings are sorted by filename.

    Precondition:
    <path> is a valid path
    """
    files = (file for file in os.listdir(path) if not file.startswith("."))
    return sorted(files)


def dir_tree_from_nested_tuple(obj: tuple[str, int | list]) -> DirectoryTree:
    """
    Return a DirectoryTree object representing the file system tree structure
    contained in the given nested <obj>.

    Precondition:

    obj represents a valid file system tree structure, with a directory at
    its root.
    """
    if not obj[1]:
        return DirectoryTree(obj[0], [])
    else:
        subtree = []
        for filename in obj[1]:
            if isinstance(filename[1], int):
                subtree.append(FileTree(filename[0], filename[1]))
            else:
                subtree.append(dir_tree_from_nested_tuple(filename))
        return DirectoryTree(obj[0], subtree)


def url_from_moves(moves: list[str]) -> str:
    """
    Returns a lichess url corresponding to the board position
    specified by the sequence of <moves>.

    Precondition:
    <moves> must be a list of uci formatted strings (e.g. [e2e4, e7e5])

    >>> url_from_moves(['e2e4']).replace('https://lichess.org/analysis/','')
    'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR_b_KQkq_-_0_1'
    """
    import chess
    board = chess.Board()
    for move in moves:
        board.push(chess.Move.from_uci(move))
    url = 'https://lichess.org/analysis/' + board.fen().replace(' ', '_')
    return url


def moves_to_nested_dict(moves: list[list[str]]) -> dict[tuple[str,
                                                         int], dict]:
    """
    Convert <moves> into a nested dictionary representing the sequence of moves
    made in the games.

    Each list in <moves> corresponds to one game, with the i'th str being the
    i'th move of the game.

    The nested dictionary's keys are tuples containing the string representing
    the move made on that turn and an integer indicating how many games ended
    immediately after this move. See the docstring example below.

    The values of each nested dictionary are themselves nested dictionaries of
    this structure. An empty dictionary is stored as the value for a move that
    will correspond to a leaf

    >>> moves_to_nested_dict([[]])  # empty lists are ignored
    {}
    >>> moves_to_nested_dict([])
    {}
    >>> moves_to_nested_dict([['a'], []])
    {('a', 1): {}}
    >>> d = moves_to_nested_dict([["a", "b", "c"],
    ...                           ["a", "b"], ["d", "e"], ["d", "e"]])
    >>> d
    {('a', 0): {('b', 1): {('c', 1): {}}}, ('d', 0): {('e', 2): {}}}
    >>> d = moves_to_nested_dict([
    ...    ["a", "b", "c"], ["a", "b"], ["d", "e", "a"], ["d", "e"]])
    >>> d
    {('a', 0): {('b', 1): {('c', 1): {}}}, ('d', 0): {('e', 1): {('a', 1): {}}}}
    """
    if len(moves) == 0 or len(moves[0]) == 0:
        return {}
    elif len(moves) == 1 and len(moves[0]) == 1:
        return {(moves[0][0], 1): {}}
    else:
        d = {}
        for lst in moves:
            if not lst == []:
                d[lst[0]] = []
        for lst in moves:
            if not lst == []:
                d[lst[0]].append(lst[1:])
        nested_d = {}
        for move in d:
            nested_d[(move, d[move].count([]))] = moves_to_nested_dict(d[move])
        return nested_d


########
# TMTree and subclasses
########

class TMTree:
    """A TreeMappableTree: a tree that is compatible with the treemap
    visualiser.

    === Public Attributes ===
    rect:
        The pygame rectangle representing this node in the treemap
        visualization. A pygame rectangle is of the form:
        (x, y, width, height) where (x, y) is the upper, left corner of
        the rectangle.
    data_size:
        The size of the data represented by this tree.

    === Private Attributes ===
    _colour:
        The RGB colour value of the root of this tree.
    _name:
        The root value of this tree.
    _subtrees:
        The subtrees of this tree.
    _parent_tree:
        The parent tree of this tree; that is to say, the tree that contains
        this tree as a subtree, or None if this tree is the root.
    _expanded:
        Whether this tree is considered expanded for visualization.

    === Representation Invariants ===
    - data_size > 0
    - _name is a non-empty string
    - If _subtrees is not empty, then data_size is greater than or equal to the
    sum of the data_size of each subtree.

    - _colour's elements are each in the range 0-255, inclusive

    - if _parent_tree is not None, then self is in _parent_tree._subtrees
    - if _parent_tree is None, this is a root of a tree (no parent)
    - this tree is the _parent_tree for each tree _subtrees

    - if _expanded is True, then _parent_tree._expanded is True
    - if _expanded is False, then _expanded is False for **every** subtree
      in _subtrees
    - if _subtrees is empty, then _expanded is False
    """

    rect: Optional[tuple[int, int, int, int]]
    data_size: int
    _colour: tuple[int, int, int]
    _name: str
    _subtrees: list[TMTree]
    _parent_tree: Optional[TMTree]
    _expanded: bool

    def __init__(self, name: str, subtrees: list[TMTree],
                 data_size: int = 1) -> None:
        """Initialize a new TMTree with a random colour and the provided <name>.

        This tree's data_size attribute is initialized to be
        the sum of the sizes of its <subtrees> + <data_size>.

        The tree is initially expanded, unless it has no subtrees.

        The rect attribute is initially None.

        This tree is initially a root (has no parent).

        Preconditions:
        <name> is a non-empty string
        <data_size> >= 0
        if <subtrees> is empty, then <data_size> > 0
        all trees in <subtrees> are roots (they don't have parents)

        >>> t1 = TMTree('B', [], 5)
        >>> t1.rect is None
        True
        >>> t1.data_size
        5
        >>> t2 = TMTree('A', [t1], 1)
        >>> t2.rect is None
        True
        >>> t2.data_size
        6
        """
        self._name = name
        self.rect = None
        self._parent_tree = None
        self._colour = (randint(0, 255), randint(0, 255), randint(0, 255))
        self._subtrees = subtrees
        self.data_size = data_size
        for subtree in subtrees:
            self.data_size += subtree.data_size
            subtree._parent_tree = self
        if len(subtrees) == 0:
            self._expanded = False
        else:
            self._expanded = True

    def is_displayed_tree_leaf(self) -> bool:
        """
        Return whether this tree is a leaf in the displayed-tree.

        >>> t1 = TMTree('B', [], 5)
        >>> t1.is_displayed_tree_leaf()
        True
        >>> t2 = TMTree('A', [t1], 1)
        >>> t1.is_displayed_tree_leaf()
        True
        >>> t2.is_displayed_tree_leaf()
        False
        """
        parent = self._parent_tree
        if parent is None:
            if self._expanded is False:
                return True
            else:
                return False
        else:
            if parent._expanded and not self._expanded:
                return True
            else:
                return False

    # Methods for the string representation
    def get_path_string(self) -> str:
        """
        Return a string representing the path containing this tree
        and its ancestors, using the separator for this tree between each
        tree's name, and the suffic for this tree at the end.

        >>> d1 = TMTree('C1', [], 5)
        >>> d2 = TMTree('C2', [d1], 1)
        >>> d3 = TMTree('C', [d2], 1)
        >>> d3.get_path_string()
        'C(7) None'
        >>> d1.get_path_string()
        'C | C2 | C1(5) None'
        """
        suffix = self.get_suffix()
        curr = self._parent_tree
        path_string = self._name + suffix
        while curr is not None:
            path_string = curr._name + self.get_separator() + path_string
            curr = curr._parent_tree
        return path_string

    def get_separator(self) -> str:
        """
        Return the string used to separate names in the string
        representation of a path from the tree root to this tree.

        >>> TMTree('root', []).get_separator()
        ' | '
        """
        return ' | '

    def get_suffix(self) -> str:
        """Return the string used at the end of the string representation of
        a path from the tree root to this tree.

        >>> TMTree('root', []).get_suffix()
        '(1) None'
        """
        return f"({self.data_size}) {self.rect}"

    def __str__(self) -> str:
        """
        Return a string representation of the tree rooted at <self>.

        >>> d1 = TMTree('C1', [], 5)
        >>> d2 = TMTree('C2', [d1], 1)
        >>> d3 = TMTree('C', [d2], 1)
        >>> print(d3)
        C | (7) None
            C2 | (6) None
                C1(5) None
        """
        return self._str_helper().rstrip()  # rstrip removes the trailing '\n'

    def _str_helper(self, indent: int = 0) -> str:
        """
        Recursive helper for __str__
        <indent> specifies the indentation level.
        """
        tab = "    "  # four spaces
        rslt = f"{indent * tab}{self._name}"
        if self._subtrees:
            rslt += self.get_separator()
        rslt += f"({self.data_size}) {self.rect}\n"
        for subtree in self._subtrees:
            rslt += subtree._str_helper(indent + 1)
        return rslt

    def update_rectangles(self, rect: tuple[int, int, int, int]) -> None:
        """
        Update the rectangles in this tree and its descendents using the
        treemap algorithm to fill the area defined by pygame rectangle <rect>.

        precondition: the rectangle given is a valid one

        >>> t1 = TMTree('B', [], 5)
        >>> t2 = TMTree('A', [t1], 1)
        >>> t2.update_rectangles((0, 0, 100, 200))
        >>> t2.rect
        (0, 0, 100, 200)
        >>> t1.rect
        (0, 0, 100, 200)
        >>> s1 = TMTree('C1', [], 5)
        >>> s2 = TMTree('C2', [], 15)
        >>> t3 = TMTree('C', [s1, s2], 1)
        >>> t3.update_rectangles((0, 0, 100, 200))
        >>> s1.rect
        (0, 0, 100, 50)
        >>> s2.rect
        (0, 50, 100, 150)
        >>> t3.rect
        (0, 0, 100, 200)
        """
        total = 0
        for subtree in self._subtrees:
            total += subtree.data_size
        if not self._subtrees:
            self.rect = rect
        elif len(self._subtrees) == 1:
            self.rect = rect
            self._subtrees[0].update_rectangles(rect)
        else:
            self.rect = rect
            num_subtrees = len(self._subtrees)
            upper_left = (rect[0], rect[1])
            if rect[2] > rect[3]:
                for i in range(num_subtrees - 1):
                    prop = (self._subtrees[i].data_size * rect[2]) / total
                    width = math.floor(prop)
                    self._subtrees[i].update_rectangles(
                        (upper_left[0], upper_left[1], width, rect[3]))
                    upper_left = (upper_left[0] + width, upper_left[1])
                width_remain = rect[2] + rect[0] - upper_left[0]
                self._subtrees[num_subtrees - 1].update_rectangles(
                    (upper_left[0], upper_left[1], width_remain, rect[3]))
            else:
                for i in range(num_subtrees - 1):
                    prop = (self._subtrees[i].data_size * rect[3]) / total
                    height = math.floor(prop)
                    self._subtrees[i].update_rectangles(
                        (upper_left[0], upper_left[1], rect[2], height))
                    upper_left = (upper_left[0], upper_left[1] + height)
                height_remain = rect[1] + rect[3] - upper_left[1]
                self._subtrees[num_subtrees - 1].update_rectangles(
                    (upper_left[0], upper_left[1], rect[2], height_remain))

    def get_rectangles(self) -> list[tuple[tuple[int, int, int, int],
                                           tuple[int, int, int]]]:
        """Return a list with tuples for every leaf in the displayed-tree
        rooted at this tree. Each tuple consists of a tuple that defines the
        appropriate pygame rectangle to display for a leaf, and the colour
        to fill it with.

        >>> t1 = TMTree('B', [], 5)
        >>> t2 = TMTree('A', [t1], 1)
        >>> t2.update_rectangles((0, 0, 100, 200))
        >>> t2.get_rectangles()[0][0]
        (0, 0, 100, 200)
        >>> s1 = TMTree('C1', [], 5)
        >>> s2 = TMTree('C2', [], 15)
        >>> t3 = TMTree('C', [s1, s2], 1)
        >>> t3.update_rectangles((0, 0, 100, 200))
        >>> rectangles = t3.get_rectangles()
        >>> rectangles[0][0]
        (0, 0, 100, 50)
        >>> rectangles[1][0]
        (0, 50, 100, 150)
        """
        if self._parent_tree is not None:
            if not self._parent_tree._expanded:
                return []
            elif not self._expanded:
                return [(self.rect, self._colour)]
            else:
                list_rect = []
                for subtree in self._subtrees:
                    list_rect += subtree.get_rectangles()
                return list_rect
        else:
            if not self._expanded:
                return [(self.rect, self._colour)]
            else:
                list_rect = []
                for subtree in self._subtrees:
                    list_rect += subtree.get_rectangles()
                return list_rect

    def get_tree_at_position(self, pos: tuple[int, int]) -> Optional[TMTree]:
        """
        Return the leaf in the displayed-tree rooted at this tree whose
        rectangle contains position <pos>, or None if <pos> is outside this
        tree's rectangle.

        If <pos> is on the shared edge between two rectangles, return the
        tree represented by the rectangle that is first encountered when
        traversing the TMTree in the natural order.

        Preconditions:
        update_rectangles has previously been called on the root of the tree
        that self is part of.

        self is part of the displayed-tree.

        >>> t1 = TMTree('B', [], 5)
        >>> t2 = TMTree('A', [t1], 1)
        >>> t2.update_rectangles((0, 0, 100, 200))
        >>> t1.get_tree_at_position((10, 10)) is t1
        True
        >>> t2.get_tree_at_position((10, 10)) is t1
        True
        >>> t2.get_tree_at_position((500, 500)) is None
        True
        >>> s1 = TMTree('C1', [], 5)
        >>> s2 = TMTree('C2', [], 15)
        >>> t3 = TMTree('C', [s1, s2], 1)
        >>> t3.update_rectangles((0, 0, 100, 200))
        >>> t3.get_tree_at_position((0, 0)) is s1
        True
        >>> t3.get_tree_at_position((100, 100)) is s2
        True
        """
        if pos[0] < self.rect[0] or pos[0] > self.rect[0] + self.rect[2]:
            return None
        elif pos[1] < self.rect[1] or pos[1] > self.rect[1] + self.rect[3]:
            return None
        elif not self._expanded:
            return self
        else:
            for subtree in self._subtrees:
                result = subtree.get_tree_at_position(pos)
                if result is not None:
                    return result
            return None

    def expand(self) -> TMTree:
        """
        Set this tree to be expanded, and return its first (leftmost) subtree.

        But if this tree has no subtrees, do nothing (since a leaf can't
        be expanded), and return self.

        Precondition:
        self is part of the displayed-tree

        >>> s1 = TMTree('C1', [], 5)
        >>> s2 = TMTree('C2', [], 15)
        >>> t3 = TMTree('C', [s1, s2], 1)
        >>> t3._expanded = False
        >>> s1.is_displayed_tree_leaf()
        False
        >>> t3.expand() is s1
        True
        >>> s1.is_displayed_tree_leaf()
        True
        """
        if not self._subtrees:
            return self
        else:
            self._expanded = True
            return self._subtrees[0]

    def expand_all(self) -> TMTree:
        """
        Fully expand this TMTree and ALL of its subtrees.

        Return the "last" TMTree. By "last", we mean the rightmost subtree of
        the last TMTree that is expanded when we traverse the TMTree in the
        usual "for subtree in self._subtrees" order.

        If self has no subtrees, return self.

        Precondition:
        self is a part of the displayed-tree

        >>> d1 = TMTree('C1', [], 5)
        >>> d2 = TMTree('C2', [d1], 1)
        >>> d3 = TMTree('C', [d2], 1)
        >>> d3._expanded = False
        >>> d2._expanded = False
        >>> d1.is_displayed_tree_leaf()
        False
        >>> d2.is_displayed_tree_leaf()
        False
        >>> d3.expand_all() is d1
        True
        >>> d1.is_displayed_tree_leaf()
        True
        >>> d2.is_displayed_tree_leaf()
        False
        """
        if not self._subtrees:
            return self
        else:
            self._expanded = True
            right_most = []
            for subtree in self._subtrees:
                right_most.append(subtree.expand_all())
            return right_most[len(right_most) - 1]

    def collapse(self) -> TMTree:
        """
        Remove self from the displayed-tree and return self's parent.

        If this node is the root of the whole tree, do nothing and return self.

        Precondition:
        self is a leaf of the displayed-tree

        >>> d1 = TMTree('C1', [], 5)
        >>> d2 = TMTree('C2', [d1], 1)
        >>> d1.is_displayed_tree_leaf()
        True
        >>> d2.is_displayed_tree_leaf()
        False
        >>> d1.collapse() is d2
        True
        >>> d1.is_displayed_tree_leaf()
        False
        >>> d2.is_displayed_tree_leaf()
        True
        """
        if self._parent_tree is None:
            return self
        else:
            self._parent_tree._expanded = False
            for subtree in self._parent_tree._subtrees:
                subtree._unexpanded()
            return self._parent_tree

    def _unexpanded(self) -> None:
        """
        Set _expanded to be False for this TMTree and set _expanded to be False
        for all the descendants of this tree. If self has no subtrees, then it
        is naturally not expanded by RI, so do nothing in this case.
        """
        if not self._subtrees:
            pass
        else:
            self._expanded = False
            for subtree in self._subtrees:
                subtree._unexpanded()

    def collapse_all(self) -> TMTree:
        """
        Collapse the entire displayed-tree to a single node (the root).
        Return the root of the tree that self is a part of.

        Precondition:
        self is a leaf of the displayed-tree

        >>> d1 = TMTree('C1', [], 5)
        >>> d2 = TMTree('C2', [d1], 1)
        >>> d3 = TMTree('C', [d2], 1)
        >>> d1.is_displayed_tree_leaf()
        True
        >>> d1.collapse_all() is d3
        True
        >>> d1.is_displayed_tree_leaf()
        False
        >>> d2.is_displayed_tree_leaf()
        False
        >>> d3.is_displayed_tree_leaf()
        True
        """
        if self._parent_tree is None:
            return self
        else:
            curr = self
            while curr._parent_tree is not None:
                curr = curr.collapse()
            return curr

    def move(self, destination: TMTree) -> None:
        """
        Move this tree to be the last subtree of <destination>.

        Preconditions:
        both self and destination are leaves in the displayed-tree

        self is not destination

        update_rectangles has previously been called on the root of the tree
        that self is part of.

        Moving self will not result in self's parent having a data size of zero.

        >>> s1 = TMTree('C1', [], 5)
        >>> s2 = TMTree('C2', [], 15)
        >>> t3 = TMTree('C', [s1, s2], 1)
        >>> t3.update_rectangles((0, 0, 100, 200))
        >>> s1.is_displayed_tree_leaf()
        True
        >>> s2.is_displayed_tree_leaf()
        True
        >>> s2.move(s1)
        >>> s2.rect
        (0, 0, 100, 200)
        >>> s1.data_size
        20
        >>> t3.data_size
        21
        >>> t3.get_tree_at_position((0, 0)) is s2
        True
        >>> s1.is_displayed_tree_leaf()
        False
        >>> s2.is_displayed_tree_leaf()
        True
        """
        if self is not destination:
            destination._subtrees.append(self)
            if len(self._parent_tree._subtrees) < 2:
                self._parent_tree._expanded = False
            self._parent_tree._subtrees.remove(self)
            curr1 = self
            while curr1._parent_tree is not None:
                curr1._parent_tree.data_size = \
                    curr1._parent_tree.data_size - self.data_size
                curr1 = curr1._parent_tree
            self._parent_tree = destination
            destination._expanded = True
            curr2 = self
            while curr2._parent_tree is not None:
                curr2._parent_tree.data_size += self.data_size
                curr2 = curr2._parent_tree
            curr2.update_rectangles((curr2.rect[0],
                                     curr2.rect[1],
                                     curr2.rect[2], curr2.rect[3]))

    def change_size(self, factor: float) -> None:
        """
        Change the value of this tree's data_size attribute by <factor> of
        its current size.

        If the change results in the data_size being less than the sum of its
        subtree data sizes, then the data_size is set to the sum of its
        subtree data sizes (the smallest possible value allowed).

        If the change results in the data_size being less
        than 1, the data_size is set to 1.

        Precondition:
        <factor> != 0

        self is a leaf of the displayed-tree

        update_rectangles has previously been called on the root of the tree
        that self is part of.

        >>> s1 = TMTree('C1', [], 5)
        >>> s2 = TMTree('C2', [], 15)
        >>> t3 = TMTree('C', [s1, s2], 1)
        >>> t3.update_rectangles((0, 0, 100, 200))
        >>> s2.change_size(-2/3)
        >>> s2.data_size
        5
        >>> t3.data_size
        11
        >>> s2.rect
        (0, 100, 100, 100)
        """
        if factor < 0:
            size = math.floor(factor * self.data_size)
        else:
            size = math.ceil(factor * self.data_size)
        old_data_size = self.data_size
        new_data_size = self.data_size + size
        if not self._subtrees:
            if new_data_size < 1:
                self.data_size = 1
            else:
                self.data_size = new_data_size
        else:
            subtree_size = 0
            for subtree in self._subtrees:
                subtree_size += subtree.data_size
            if new_data_size < subtree_size:
                self.data_size = subtree_size
            else:
                self.data_size = new_data_size
        curr = self
        while curr._parent_tree is not None:
            curr._parent_tree.data_size += (self.data_size - old_data_size)
            curr = curr._parent_tree
        curr.update_rectangles((curr.rect[0], curr.rect[1], curr.rect[2],
                                curr.rect[3]))


######################
# subclasses of TMTree
######################

class FileTree(TMTree):
    """
    A tree representation of a file in a file system, for use with
    treemap visualizer.

    === Public Attributes ===
    rect:
        The pygame rectangle representing this node/file in the treemap
        visualization. A pygame rectangle is of the form:
        (x, y, width, height) where (x, y) is the upper, left corner of
        the rectangle.
    data_size:
        The data size of the file.

    === Private Attributes ===
    _colour:
        The RGB colour value of the root of this file tree.
    _name:
        The name of the file.
    _subtrees:
        The subtrees of this file tree which is always empty.
    _parent_tree:
        The directory tree of this file tree; that is to say,
        the directory tree that contains this file tree as a subtree,
        or None if this file tree is the root.
    _expanded:
        Whether this file tree is considered expanded for visualization. It is
        always false since there are never subtrees.

    === Representation Invariants ===
    -len(self._subtrees) = 0
    -self._expanded = False

    The _name attribute stores the *name* of the file, not its full
    path.
    """

    rect: Optional[tuple[int, int, int, int]]
    data_size: int
    _colour: tuple[int, int, int]
    _name: str
    _subtrees: list[TMTree]
    _parent_tree: Optional[DirectoryTree]
    _expanded: bool

    def __init__(self, name: str, data_size: int) -> None:
        """
        Initialize new file tree with name <name> and random color.
        """
        TMTree.__init__(self, name, [], data_size)

    def get_separator(self) -> str:
        """
        Return the string used to separate names in the string
        representation of a path from the tree root to this tree.
        """
        return os.path.sep

    def get_suffix(self) -> str:
        """Return the string used at the end of the string representation of
        a path from the tree root to this tree.
        """
        return " (file)"

    def move(self, destination: TMTree) -> None:
        """
        Move this file tree to be the last subtree of <destination>.
        """
        if isinstance(destination, FileTree):
            raise OperationNotSupportedError
        else:
            TMTree.move(self, destination)


class DirectoryTree(TMTree):
    """A tree representation of a directory in a file system for use with
    our treemap visualizer.

    === Public Attributes ===
    rect:
        The pygame rectangle representing this directory tree in the treemap
        visualization. A pygame rectangle is of the form:
        (x, y, width, height) where (x, y) is the upper, left corner of
        the rectangle.
    data_size:
        The data size of this directory tree

    === Private Attributes ===
    _colour:
        The RGB colour value of the root of this directory tree.
    _name:
        The name of this directory.
    _subtrees:
        The subtrees of this directory tree.
    _parent_tree:
        The parent tree of this tree; that is to say, the tree that contains
        this tree as a subtree, or None if this tree is the root.
    _expanded:
        Whether this tree is considered expanded for visualization.

    The _name attribute stores the *name* of the directory, not its full
    path.

    The _name attribute stores the *name* of the file, not its full
    path.

    >>> my_dir = dir_tree_from_nested_tuple((
    ...     (".", [
    ...         ("documents", [("report.pdf", 13), ("data.xlsx", 10)]),
    ...         ("images", [("vacation", [("beach.png", 5)])]),
    ...         ("my_song.mp3", 14),
    ...         ("empty_dir", [])
    ...     ])
    ... ))
    >>> my_dir.data_size
    47
    >>> len(my_dir._subtrees)
    4
    >>> documents = my_dir._subtrees[0]
    >>> isinstance(documents, DirectoryTree)
    True
    >>> isinstance(documents, TMTree)
    True
    >>> images = my_dir._subtrees[1]
    >>> empty_dir = my_dir._subtrees[3]
    >>> report_file = documents._subtrees[0]
    >>> data_file = documents._subtrees[1]
    >>> isinstance(data_file, FileTree)
    True
    >>> isinstance(data_file, TMTree)
    True
    >>> documents.data_size
    24
    >>> images.data_size
    7
    >>> str(my_dir) == DIRECTORYTREE_EXAMPLE_RESULT
    True
    >>> path_string = documents.get_path_string()
    >>> path_string == './documents (directory)'.replace("/", os.path.sep)
    True
    >>> path_string = data_file.get_path_string()
    >>> path_string == './documents/data.xlsx (file)'.replace("/", os.path.sep)
    True
    >>> my_dir.update_rectangles((0, 0, 200, 400))  # call update before move.
    >>> try:
    ...     data_file.move(report_file)  # can't because report is not a dir
    ...     raised_error = False
    ... except OperationNotSupportedError:
    ...     raised_error = True
    >>> raised_error
    True
    >>> path_string = data_file.get_path_string()
    >>> path_string == './documents/data.xlsx (file)'.replace("/", os.path.sep)
    True
    >>> data_file.move(empty_dir)  # can move; empty_dir is a leaf and directory
    >>> path_string = data_file.get_path_string()
    >>> path_string == './empty_dir/data.xlsx (file)'.replace("/", os.path.sep)
    True
    """

    rect: Optional[tuple[int, int, int, int]]
    data_size: int
    _colour: tuple[int, int, int]
    _name: str
    _subtrees: list[TMTree]
    _parent_tree: Optional[DirectoryTree]
    _expanded: bool

    def __init__(self, name: str, subtrees: list[TMTree]) -> None:
        """
        Initialize new directory tree with name <name> and random color.
        """
        TMTree.__init__(self, name, subtrees, 1)

    def get_separator(self) -> str:
        """
        Return the string used to separate names in the string
        representation of a path from the tree root to this tree.
        """
        return os.path.sep

    def get_suffix(self) -> str:
        """Return the string used at the end of the string representation of
        a path from the tree root to this tree.
        """
        return " (directory)"

    def move(self, destination: TMTree) -> None:
        """
        Move this Directory tree to be the last subtree of <destination>.
        """
        if isinstance(destination, FileTree):
            raise OperationNotSupportedError
        else:
            TMTree.move(self, destination)

    def change_size(self, factor: float) -> None:
        """
        DirectoryTree objects can NOT be resized. Attempting to change the size
        of a directory will raise an OperationNotSupportedError.
        """
        raise OperationNotSupportedError


class ChessTree(TMTree):
    """
    A chess tree representing sequences of moves in a collection of chess games
    """
    # === Private Attributes ===
    # _white_to_play: True iff it is white's turn to make the next move.

    _white_to_play: bool

    def __init__(self, move_dict: dict[tuple[str, int], dict],
                 last_move: str = "-",
                 white_to_play: bool = True,
                 num_games_ended: int = 0) -> None:
        """
        Initialize this ChessTree given the nested <move_dict>. See the
        moves_to_nested_dict function for the exact format of <move_dict>.

        <last_move> represents the move that was last played. The root of the
        tree has a last move of '-' (default parameter value).

        <white_to_play> indicates where it is white's turn (True) or black's
        turn (False).

        <num_games_ended> indicates how many games ended after the sequence of
        moves corresponding to this ChessTree.

        Preconditions:
        <move_dict> contains a valid representation of a ChessTree.
        <last_move> is a non-empty string.
        <num_games_ended> > 0 if the resulting ChessTree will be a leaf,
        since at least one game must have ended for it to be a leaf.

        >>> ct = ChessTree({('e2e4', 0) : {('e7e5', 1) : {}}})
        >>> ct.is_displayed_tree_leaf()
        False
        >>> ct.data_size
        1
        >>> ct.rect is None
        True
        >>> print(ct)
        - | (1) None
            e2e4 | (1) None
                e7e5(1) None
        """
        self._white_to_play = white_to_play
        subtrees = []
        for move in move_dict:
            subtrees.append(ChessTree(move_dict[move],
                                      move[0], not white_to_play, move[1]))
        TMTree.__init__(self, last_move, subtrees, num_games_ended)

    def get_suffix(self) -> str:
        """
        Return ' (white to play)' if white is next to move,
        ' (black to play)' if black is next to move
        and ' (end)' if this ChessTree has no subtrees.

        >>> ct = ChessTree({('e2e4', 0) : {('e7e5', 1) : {}}})
        >>> ct.get_suffix()
        ' (white to play)'
        >>> last_node = ct.expand_all()
        >>> last_node.get_suffix()
        ' (end)'
        >>> second_last_node = last_node.collapse()
        >>> second_last_node.get_suffix()
        ' (black to play)'
        """
        if not self._subtrees:
            return ' (end)'
        else:
            if self._white_to_play:
                return ' (white to play)'
            else:
                return ' (black to play)'

    def open_page(self) -> None:
        """
        Open a web browser to a lichess url corresponding
        to the board state of this tree.

        # >>> ct = ChessTree({('e2e4', 1): {}})
        # >>> ct.open_page()  # will open an analysis board with no moves made
        """
        path = self.get_path_string()
        path = path.split(self.get_separator())[1:]  # drop the leading '- | '
        if not path:  # no moves made!
            moves = []
        else:
            path[-1] = path[-1].split(" ")[0]  # truncate the suffix
            moves = path  # renaming for clarity of interpretation
        print(f'Opening game after moves: {"-".join(moves)}')
        webbrowser.open(url_from_moves(moves))

    def change_size(self, factor: float) -> None:
        """
        ChessTree objects can NOT be resized. Attempting to change the size
        of a directory will raise an OperationNotSupportedError.
        """
        raise OperationNotSupportedError

    def move(self, destination: TMTree) -> None:
        """
        ChessTree objects can NOT be moved. Attempting to change the size
        of a directory will raise an OperationNotSupportedError.
        """
        raise OperationNotSupportedError


if __name__ == '__main__':
    print("Very small TMTree example")
    s1 = TMTree('C1', [], 5)
    s2 = TMTree('C2', [], 15)
    t3 = TMTree('C', [s1, s2], 1)

    t3.update_rectangles((0, 0, 100, 200))
    print(t3)

    print("\n\nWorksheet TMTree example")
    ex_tree = example_tree()
    print(ex_tree)

    print('=' * 80)
    
    nested_tuple = path_to_nested_tuple("example-directory")
    tree = dir_tree_from_nested_tuple(nested_tuple)
    
    tree.update_rectangles((0, 0, 100, 200))
    print(tree)

    print('=' * 80)

    with open('wgm_10.json', 'r') as game_file:
        GAME_LIST = json.load(game_file)
    games = moves_to_nested_dict(GAME_LIST)
    tree = ChessTree(games)
   
    print(tree.expand_all().get_path_string())
