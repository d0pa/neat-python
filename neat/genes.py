"""Handles genes coding for node and connection attributes."""
import warnings
from random import random

from neat.attributes import FloatAttribute, BoolAttribute, FuncAttribute

# TODO: There is probably a lot of room for simplification of these classes using metaprogramming.
# TODO: Evaluate using __slots__ for performance/memory usage improvement.


class BaseGene(object):
    """
    Handles functions shared by multiple types of genes (both node and connection),
    including crossover and calling mutation methods.
    """
    def __init__(self, key):
        self.key = key

    def __str__(self):
        attrib = ['key'] + [a.name for a in self._gene_attributes]
        attrib = ['{0}={1}'.format(a, repr(getattr(self, a))) for a in attrib]
        return '{0}({1})'.format(self.__class__.__name__, ", ".join(attrib))

    def __lt__(self, other):
        assert isinstance(self.key,type(other.key)), "Cannot compare keys {0!r} and {1!r}".format(
            self.key,other.key)
        return self.key < other.key

    @classmethod
    def parse_config(cls, config, param_dict):
        pass

    @classmethod
    def get_config_params(cls):
        params = []
        if not hasattr(cls, '_gene_attributes'):
            setattr(cls, '_gene_attributes', getattr(cls, '__gene_attributes__'))
            warnings.warn(
                "Class '{!s}' {!r} needs '_gene_attributes' not '__gene_attributes__'".format(
                    cls.__name__,cls),
                DeprecationWarning)
        for a in cls._gene_attributes:
            params += a.get_config_params()
        return params

    def init_attributes(self, config):
        for a in self._gene_attributes:
            setattr(self, a.name, a.init_value(config))

    def mutate(self, config):
        for a in self._gene_attributes:
            v = getattr(self, a.name)
            setattr(self, a.name, a.mutate_value(v, config))

    def copy(self):
        new_gene = self.__class__(self.key)
        for a in self._gene_attributes:
            value = getattr(self, a.name)
            if hasattr(value, 'copy'):
                setattr(new_gene, a.name, value.copy())
            else:
                setattr(new_gene, a.name, value)
        return new_gene

    def __copy__(self):
        return self.copy()

    def crossover(self, gene2):
        """ Creates a new gene randomly inheriting attributes from its parents."""
        assert self.key == gene2.key

        # Note: we use "a if random() > 0.5 else b" instead of choice((a, b))
        # here because `choice` is substantially slower.
        new_gene = self.__class__(self.key)
        for a in self._gene_attributes:
            if random() > 0.5:
                value = getattr(self, a.name)
                if hasattr(value, 'copy'):
                    setattr(new_gene, a.name, value.copy())
                else:
                    setattr(new_gene, a.name, value)
            else:
                gene2_attr = getattr(gene2, a.name)
                if hasattr(gene2_attr, 'copy'):
                    setattr(new_gene, a.name, gene2_attr.copy())
                else:
                    setattr(new_gene, a.name, gene2_attr)
        return new_gene


# TODO: Should these be in the nn module?  iznn and ctrnn can have additional attributes.


class DefaultNodeGene(BaseGene):
    _gene_attributes = [FloatAttribute('bias'),
                        FloatAttribute('response'),
                        FuncAttribute('activation', options='sigmoid'),
                        FuncAttribute('aggregation', options='sum')]

    def __init__(self, key):
        assert isinstance(key, int), "DefaultNodeGene key must be an int, not {!r}".format(
            key)
        BaseGene.__init__(self, key)

    def distance(self, other, config):
        """Returns the genetic distance between two node genes."""
        d = abs(self.bias - other.bias) + abs(self.response - other.response)
        if hasattr(self.activation, 'distance'):
            d += self.activation.distance(other.activation)
        elif self.activation != other.activation:
            d += 1.0

        if hasattr(self.aggregation, 'distance'):
            d += self.aggregation.distance(other.aggregation)
        elif self.aggregation != other.aggregation:
            d += 1.0
        
        return d * config.compatibility_weight_coefficient


# TODO: Do an ablation study to determine whether the enabled setting is
# important--presumably mutations that set the weight to near zero could
# provide a similar effect depending on the weight range, mutation rate,
# and aggregation function. (Most obviously, a near-zero weight for the
# `product` aggregation function is rather more important than one giving
# an output of 1 from the connection, for instance!)
class DefaultConnectionGene(BaseGene):
    _gene_attributes = [FloatAttribute('weight'),
                        BoolAttribute('enabled')]

    def __init__(self, key):
        assert isinstance(key, tuple), "DefaultConnectionGene key must be a tuple, not {!r}".format(
            key)
        BaseGene.__init__(self, key)

    def distance(self, other, config):
        """Returns the genetic distance between two connection genes."""
        d = abs(self.weight - other.weight)
        if self.enabled != other.enabled:
            d += 1.0
        return d * config.compatibility_weight_coefficient

