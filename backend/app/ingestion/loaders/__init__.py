from .base import RawDocument, Loader
from .nice import NICELLoader
from .medlineplus import MedlinePlusLoader
from .knmf import KNMFLoader

ALL_LOADERS = [
    NICELLoader(),
    MedlinePlusLoader(),
    KNMFLoader(),
]


def find_loader(path):
    for loader in ALL_LOADERS:
        if loader.can_load(path):
            return loader
    return None


__all__ = [
    "RawDocument",
    "Loader",
    "ALL_LOADERS",
    "find_loader",
    "NICELLoader",
    "MedlinePlusLoader",
    "KNMFLoader",
]
