__version__ = "0.0.1"

from .data import Data

__all__ = ["Data"]

from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    pass
