# Sourced from https://realpython.com/pypi-publish-python-package/
import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="contrail-introspect-scraper",
    version="0.1.0",
    description="Collect Introspects from all Contrail nodes concurrently",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/aniruddhamonker/contrail-introspect-scrapper",
    author="Aniruddh Amonker",
    author_email="aniruddh.amonker@live.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6.8",
    ],
    packages=["ContrailIntrospectScrape", "ContrailIntrospectCli"],
    include_package_data=True,
    install_requires=["BeautifulSoup", "html5lib"],
    entry_points={
        "console_scripts": [
            "scrape=src.ContrailIntrospectScrape.__main__", "scrape-ist=src.ContrailIntrospectCli.ist:main"
        ]
    },
)