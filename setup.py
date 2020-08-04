#! /usr/bin/env python
import os
from setuptools import setup

CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: BSD License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

README_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md")
with open(README_PATH, "r", encoding="utf8") as f:
    README = f.read()

setup(
    name="ariadne",
    author="Mirumee Software",
    author_email="hello@mirumee.com",
    description="Ariadne is a Python library for implementing GraphQL servers.",
    long_description=README,
    long_description_content_type="text/markdown",
    license="BSD",
    version="0.12.0",
    url="https://github.com/mirumee/ariadne",
    packages=["ariadne"],
    include_package_data=True,
    install_requires=[
        "graphql-core>=3.0.0,<3.1.0",
        "starlette<0.14",
        "typing_extensions>=3.6.0",
    ],
    extras_require={"asgi-file-uploads": ["python-multipart>=0.0.5"]},
    classifiers=CLASSIFIERS,
    platforms=["any"],
    zip_safe=False,
)
