import numpy as np
from Cython.Build import cythonize
from setuptools import setup

setup(
    name="oure_physics_ckepler",
    ext_modules=cythonize(
        ["oure/physics/ckepler.pyx", "oure/risk/cfoster.pyx"],
        compiler_directives={"language_level": "3"},
    ),
    packages=[],
    include_dirs=[np.get_include()],
)
