import os
import pickle
from typing import Any


class SingletonPickler:

    """
    Pickles an initial 'seed' object into a file, upon initialization.
    The stored object is a 'singleton',so class provides an interface to both unpickle the object
    or to recreate the file, with a new object.

    Attributes
    -----------

    filename:
        The name of the file which will store the pickled object.


    Methods
    -------
    unpickle_object_from_database:
        Unpickles the singleton object from its file and returns

    create_pickled_file_with_new_object:
        Deletes the current file and recreates, pickling a new object.

    """

    def __init__(self, filename: str, seed: object):
        """

        :param filename:str a name for the file to be created
        :param seed: a python object to pickle and store in the file
        """
        self.filename = filename

        if not self._check_pickled_file_exists():
            with open(self.filename, "wb") as db:
                seed = seed
                pickle.dump(seed, db, pickle.HIGHEST_PROTOCOL)

    def _check_pickled_file_exists(self) -> bool:
        """Checks whether or not the file exists. Returns either true or false"""
        return os.path.exists(self.filename)

    def unpickle_object_from_database(self) -> Any:
        """Retrieves the single object out of the file storing it"""
        with open(self.filename, "rb") as db:
            return pickle.load(db)

    def _delete_pickled_file(self) -> None:
        """Deletes the file storing the pickled object"""
        if self._check_pickled_file_exists():
            os.remove(self.filename)

    def create_pickled_file_with_new_object(self, object_to_pickle: object) -> None:
        """
        Recreates the file storing the pickled object, after ensuring the original is deleted,
        with a new/updated object.

        :param object_to_pickle: object, a Python object
        :return: None
        """
        try:
            self._delete_pickled_file()
        except:
            raise FileNotFoundError()

        if not self._check_pickled_file_exists():
            with open(self.filename, "wb") as db:
                pickle.dump(object_to_pickle, db, pickle.HIGHEST_PROTOCOL)
