import os

from setuptools import setup


def package_files(directory):
    paths = []
    for path, directories, file_names in os.walk(directory):
        for filename in file_names:
            paths.append(os.path.join("..", path, filename))
    return paths


extra_files = package_files("lobbyclient")


setup(
    name="lobbyclient",
    version="1.0",
    packages=["lobbyclient"],
    package_data={"": extra_files},
    install_requires=[
        "yeetlong @ https://github.com/guldfisk/yeetlong/tarball/master#egg=yeetlong-1.0",
        "websocket-client",
        "websocket",
        "frozendict",
    ],
)
