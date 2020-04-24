import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="regex-jit",
    version="0.0.1",
    author="Dayton J Allen",
    description="Compiled to native code regular expressions in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/daytonallen/regex-jit",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Os Independent"
    ],
    python_requires='>=3.8'
)