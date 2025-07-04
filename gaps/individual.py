import numpy as np

from gaps import utils
from gaps.image_analysis import ImageAnalysis

from sem_consistency import compute_sem_consistency


from enum import Enum

class FitnessType(Enum):
    Similarity = 1
    Semantic = 2
    Sum = 3

class Individual(object):
    """Class representing possible solution to puzzle.

    Individual object is one of the solutions to the problem
    (possible arrangement of the puzzle's pieces).
    It is created by random shuffling initial puzzle.

    :param pieces:  Array of pieces representing initial puzzle.
    :param rows:    Number of rows in input puzzle
    :param columns: Number of columns in input puzzle

    Usage::

        >>> from gaps.individual import Individual
        >>> from gaps.image_helpers import flatten_image
        >>> pieces, rows, columns = flatten_image(...)
        >>> ind = Individual(pieces, rows, columns)

    """

    FITNESS_FACTOR = 1000

    def __init__(self, pieces, rows, columns, shuffle=True,fitness_type=FitnessType.Similarity):
        self.pieces = pieces[:]
        self.rows = rows
        self.columns = columns
        self._fitness = None

        if shuffle:
            np.random.shuffle(self.pieces)

        if fitness_type not in FitnessType:
            raise ValueError(f'Unknown fitness type {fitness_type}')
        self.fitness_type = fitness_type

        # Map piece ID to index in Individual's list
        self._piece_mapping = {
            piece.id: index for index, piece in enumerate(self.pieces)
        }

    def __getitem__(self, key):
        return self.pieces[key * self.columns : (key + 1) * self.columns]

    @property
    def fitness(self) -> float:
        """Evaluates fitness value.

        Fitness value is calculated as sum of dissimilarity measures between
        each adjacent pieces.

        """
        if self._fitness is None:
            if self.fitness_type == FitnessType.Similarity:
                self._fitness =  self._similarity()
            elif self.fitness_type == FitnessType.Semantic:
                self._fitness =  self._semantic_consistency()
            elif self.fitness_type == FitnessType.Sum:
                self._fitness =  self._similarity() + self._semantic_consistency()
            else:
                raise NotImplementedError(f'Fitness type {self.fitness_type} not implemented')
        
        #print(f'Fitness: {self._fitness}')

        return self._fitness
    
    def _similarity(self) -> float:

        fitness_value = 1 / self.FITNESS_FACTOR
        # For each two adjacent pieces in rows
        for i in range(self.rows):
            for j in range(self.columns - 1):
                ids = (self[i][j].id, self[i][j + 1].id)
                fitness_value += ImageAnalysis.get_dissimilarity(
                    ids, orientation="LR"
                )
        # For each two adjacent pieces in columns
        for i in range(self.rows - 1):
            for j in range(self.columns):
                ids = (self[i][j].id, self[i + 1][j].id)
                fitness_value += ImageAnalysis.get_dissimilarity(
                    ids, orientation="TD"
                )

        return self.FITNESS_FACTOR / fitness_value


    def _semantic_consistency(self) -> float:
        image = self.to_image()
        return compute_sem_consistency(image,(self.rows,self.columns)) * 10

    def piece_size(self):
        """Returns single piece size"""
        return self.pieces[0].size

    def piece_by_id(self, identifier):
        """ "Return specific piece from individual"""
        return self.pieces[self._piece_mapping[identifier]]

    def to_image(self):
        """Converts individual to showable image"""
        pieces = [piece.image for piece in self.pieces]
        return utils.assemble_image(pieces, self.rows, self.columns)

    def edge(self, piece_id, orientation):
        edge_index = self._piece_mapping[piece_id]

        if (orientation == "T") and (edge_index >= self.columns):
            return self.pieces[edge_index - self.columns].id

        if (orientation == "R") and (edge_index % self.columns < self.columns - 1):
            return self.pieces[edge_index + 1].id

        if (orientation == "D") and (edge_index < (self.rows - 1) * self.columns):
            return self.pieces[edge_index + self.columns].id

        if (orientation == "L") and (edge_index % self.columns > 0):
            return self.pieces[edge_index - 1].id
