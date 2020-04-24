from setuptools import setup

setup(
    setup_requires=["cffi>=1.0.0"],
    cffi_modules=["regexutil_build.py:ffibuilder"],
    install_requires=["cffi>=1.0.0"],
)