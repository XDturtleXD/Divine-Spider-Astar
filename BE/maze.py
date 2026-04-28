# maze.py
# ---------------
# Licensing Information:  You are free to use or extend this projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to the University of Illinois at Urbana-Champaign
#
# Created by Michael Abir (abir2@illinois.edu) on 08/28/2018
# Modified by Rahul Kunji (rahulsk2@illinois.edu) on 01/16/2019

"""
This file contains the Maze class, which reads in a maze file and creates
a representation of the maze that is exposed through a simple interface.
"""

import re
import copy
from collections import Counter
import os
type Pos = tuple[int, int]


class Maze:
    def __init__(self, filename: str) -> None:
        """Reads in the maze file and initializes the maze representation."""
        self.__filename: str = ''
        self.__wallChar: str = '#'
        self.__startChar: str = 'H'
        self.__objectiveChar: str = '*'
        self.__start: Pos | None = None
        self.__objective: list[Pos] = []
        self.__states_explored: int = 0
        if os.path.exists(filename):
            self.__filename = filename
            with open(filename) as f:
                lines = f.readlines()
        else:
            lines = filename.split('\n')
        lines = list(filter(lambda x: not re.match(r'^\s*$', x), lines))
        lines = [list(line.strip('\n')) for line in lines]

        if not lines:
            raise ValueError("Maze input is empty")

        expected_cols = len(lines[0])
        if any(len(line) != expected_cols for line in lines):
            raise ValueError("Maze rows must all have the same length")

        self.rows: int = len(lines)
        self.cols: int = expected_cols
        self.mazeRaw: list[list[str]] = lines

        # Check that the maze dimensions are consistent with the number of rows and columns
        if (len(self.mazeRaw) != self.rows) or (len(self.mazeRaw[0]) != self.cols):
            raise ValueError("Maze dimensions incorrect")

        # Scan the maze for the start and objective positions
        for row in range(len(self.mazeRaw)):
            for col in range(len(self.mazeRaw[0])):
                if self.mazeRaw[row][col] == self.__startChar:
                    self.__start = (row, col)
                elif self.mazeRaw[row][col] == self.__objectiveChar:
                    self.__objective.append((row, col))

    def isWall(self, row: int, col: int) -> bool:
        """Returns True if the given position is the location of a wall"""
        return self.mazeRaw[row][col] == self.__wallChar

    def isObjective(self, row: int, col: int) -> bool:
        """Returns True if the given position is the location of an objective"""
        return (row, col) in self.__objective

    def getStart(self) -> Pos:
        """Returns the starting position of the maze"""
        if self.__start is None:
            raise ValueError("Maze has no start position")
        return self.__start

    def setStart(self, start: Pos) -> None:
        self.__start = start

    def getDimensions(self) -> Pos:
        """Returns the dimensions of the maze as a (rows, cols) tuple"""
        return (self.rows, self.cols)

    def getObjectives(self) -> list[Pos]:
        """Returns the list of objective positions in the maze"""
        return copy.deepcopy(self.__objective)

    def setObjectives(self, objectives: list[Pos]) -> None:
        self.__objective = objectives

    def getStatesExplored(self) -> int:
        return self.__states_explored

    def isValidMove(self, row: int, col: int) -> bool:
        """Checks if the agent can move to the given position (i.e. it's in bounds and not a wall)"""
        return row >= 0 and row < self.rows and col >= 0 and col < self.cols and not self.isWall(row, col)

    def _getNeighbors(self, row: int, col: int) -> list[Pos]:
        """Returns a list of valid neighboring positions (i.e. up, down, left, right)"""
        possibleNeighbors: list[Pos] = [
            (row + 1, col), # down
            (row - 1, col), # up
            (row, col + 1), # right
            (row, col - 1), # left
        ]
        neighbors: list[Pos] = []
        for r, c in possibleNeighbors:
            if self.isValidMove(r, c):
                neighbors.append((r, c))
        return neighbors

    def incrementStatesExplored(self) -> None:
        self.__states_explored += 1

    def isValidPath(self, path: list[Pos]) -> str:
        """
        Checks if the given path is valid according to the maze rules.
        Returns "Valid" if the path is valid,
        otherwise returns a string describing the first rule violation encountered.
        """
        if not isinstance(path, list):
            return f"path must be list, got {type(path)}"

        if len(path) == 0:
            return "path must not be empty"

        if not isinstance(path[0], tuple):
            return f"position must be tuple, got {type(path[0])}"

        if len(path[0]) != 2:
            return f"position must be (row, col), got {path[0]}"

        # Check single hop
        for i in range(1, len(path)):
            prev = path[i - 1]
            cur = path[i]
            dr = prev[0] - cur[0]
            dc = prev[1] - cur[1]
            dist = abs(dr) + abs(dc)
            if dist > 1:
                return f"Not single hop: {prev} -> {cur}"

        # Check whether it is a valid move
        for pos in path:
            if not self.isValidMove(pos[0], pos[1]):
                return "Not valid move"

        # Check whether all goals are passed and the last position is a goal
        if not set(self.__objective).issubset(set(path)):
            return "Not all goals passed"

        # Check whether it ends at a goal
        if path[-1] not in self.__objective:
            return "Last position is not goal"

        # Check for the duplication
        if len(set(path)) != len(path):
            c = Counter(path)
            dup_dots = [p for p in set(c.elements()) if c[p] >= 2] # find the duplicated positions
            for p in dup_dots:
                indices = [i for i, dot in enumerate(path) if dot == p] # find the indices of the duplicated positions
                is_dup = True
                for i in range(len(indices) - 1):
                    for dot in path[indices[i] + 1: indices[i + 1]]:
                        if self.isObjective(dot[0], dot[1]): # if there was an objective collected, it's valid
                            is_dup = False
                            break
                if is_dup: # if there is an objective between the duplicated positions, then it is not a valid path
                    return f"Unnecessary path detected: {p}"

        return "Valid"
