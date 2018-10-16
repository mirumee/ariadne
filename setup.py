#! /usr/bin/env python
from setuptools import setup

CLASSIFIERS = [
    "Intended Audience :: Developers",
    "License :: OSI Approved :: BSD License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

setup(
    name="ariadne",
    author="Mirumee Software",
    author_email="hello@mirumee.com",
    description="A functional implementation of a Python GraphQL server",
    license="BSD",
    version="0.0.3",
    url="https://github.com/mirumee/ariadne",
    packages=["ariadne"],
    install_requires=["graphql-core>=2.1", "typing>=3.6.0"],
    classifiers=CLASSIFIERS,
    platforms=["any"],
)
