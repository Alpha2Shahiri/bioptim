from typing import Union

import numpy as np
from casadi import MX, SX, DM

from .options import OptionDict, OptionGeneric


class Mapping(OptionGeneric):
    """
    Mapping of index set to a different index set

    Example of use:
        - to_map = Mapping([0, 1, 1, 3, -1, 1], [3])
        - obj = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
        - mapped_obj = to_map.map(obj)
    Expected result:
        - mapped_obj == np.array([0.1, 0.2, 0.2, -0.4, 0, 0.1])

    Attributes
    ----------
    map_idx: list[int]
        The actual index list that links to the other set, an negative value links to a numerical 0

    Methods
    -------
    map(self, obj: list) -> list
        Apply the mapping to an obj
    len(self) -> int
        Get the len of the mapping
    """

    def __init__(self, map_idx: Union[list, tuple, range, np.ndarray], **params):
        """
        Parameters
        ----------
        map_idx: Union[list, tuple, range]
            The actual index list that links to the other set
        """
        super(Mapping, self).__init__(**params)
        self.map_idx = map_idx

    def map(self, obj: Union[tuple, list, np.ndarray, MX, SX, DM]) -> Union[np.ndarray, MX, SX, DM]:
        """
        Apply the mapping to an matrix object. The rows are mapped while the columns are preserved as is

        Parameters
        ----------
        obj: Union[np.ndarray, MX, SX, DM]
            The matrix to map

        Returns
        -------
        The list mapped
        """
        # Declare a zero filled object
        if isinstance(obj, (tuple, list)):
            obj = np.array(obj)

        if isinstance(obj, np.ndarray):
            if len(obj.shape) == 1:
                obj = obj[:, np.newaxis]
            mapped_obj = np.zeros((len(self.map_idx), obj.shape[1]))
        elif isinstance(obj, (MX, SX, DM)):
            mapped_obj = type(obj).zeros(len(self.map_idx), obj.shape[1])
        else:
            raise RuntimeError("map must be applied on np.ndarray, MX or SX")

        # Fill the positive values
        index_plus_in_origin = [abs(v) for v in self.map_idx if v is not None and v >= 0]
        index_plus_in_new = [i for i, v in enumerate(self.map_idx) if v is not None and v >= 0]
        mapped_obj[index_plus_in_new, :] = obj[index_plus_in_origin, :]  # Fill the non zeros values

        # Fill the negative values
        index_minus_in_origin = [abs(v) for v in self.map_idx if v is not None and v < 0]
        index_minus_in_new = [i for i, v in enumerate(self.map_idx) if v is not None and v < 0]
        mapped_obj[index_minus_in_new, :] = -obj[index_minus_in_origin, :]  # Fill the non zeros values

        return mapped_obj

    def __len__(self) -> int:
        """
        Get the len of the mapping

        Returns
        -------
        The len of the mapping
        """

        return len(self.map_idx)


class BiMapping(OptionGeneric):
    """
    Mapping of two index sets between each other

    Attributes
    ----------
    to_second: Mapping
        The mapping that links the first variable to the second
    to_first: Mapping
        The mapping that links the second variable to the first
    """

    def __init__(
        self,
        to_second: Union[Mapping, int, list, tuple, range],
        to_first: Union[Mapping, int, list, tuple, range],
        **params
    ):
        """
        Parameters
        ----------
        to_second: Union[Mapping, list[int], tuple[int], range]
            The mapping that links the first index set to the second
        to_first: Union[Mapping, list[int], tuple[int], range]
            The mapping that links the second index set to the first
        """
        super(BiMapping, self).__init__(**params)

        if isinstance(to_second, (list, tuple, range)):
            to_second = Mapping(map_idx=to_second)
        if isinstance(to_first, (list, tuple, range)):
            to_first = Mapping(map_idx=to_first)

        if not isinstance(to_second, Mapping):
            raise RuntimeError("to_second must be a Mapping class")
        if not isinstance(to_first, Mapping):
            raise RuntimeError("to_first must be a Mapping class")

        self.to_second = to_second
        self.to_first = to_first


class BiMappingList(OptionDict):
    def __init__(self):
        super(BiMappingList, self).__init__()

    def add(
        self,
        name: str,
        to_second: Union[Mapping, int, list, tuple, range] = None,
        to_first: Union[Mapping, int, list, tuple, range] = None,
        bimapping: BiMapping = None,
        phase: int = 0,
    ):

        """
        Add a new BiMapping to the list

        Parameters
        name: str
            The name of the new BiMapping
        to_second: Mapping
            The mapping that links the first variable to the second
        to_first: Mapping
            The mapping that links the second variable to the first
        bimapping: BiMapping
            The BiMapping to copy
        """

        if name in self:
            raise ValueError("BiMapping name should be unique")

        if isinstance(bimapping, BiMapping):
            if to_second is not None or to_first is not None:
                raise ValueError("BiMappingList should either be a to_second/to_first or an actual BiMapping")
            self.add(name, phase=phase, to_second=bimapping.to_second, to_first=bimapping.to_first)

        else:
            if to_second is None or to_first is None:
                raise ValueError("BiMappingList should either be a to_second/to_first or an actual BiMapping")
            super(BiMappingList, self)._add(
                key=name, phase=phase, option_type=BiMapping, to_second=to_second, to_first=to_first
            )

    def __getitem__(self, item) -> Union[dict, BiMapping]:
        return super(BiMappingList, self).__getitem__(item)

    def __contains__(self, item):
        return item in self.options[0].keys()
