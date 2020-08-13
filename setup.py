import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

setup(
    name="contrail-scrape",
    version="0.1.0",
    description="crawler for all the APIs of Juniper Contrail nodes",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/aniruddhamonker/contrail-scrape",
    author="Aniruddh Amonker",
    author_email="aamonker@juniper.net",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
    ],
    packages=["ContrailScrape"],
    include_package_data=True,
    install_requires=["beautifulsoup4", "tqdm", "lxml", "PrettyTable", "html5lib" ],
    entry_points={
        "console_scripts": [
            "contrail-scrape=ContrailScrape.__main__:main",
            "contrail-scrape-ist=ContrailScrape.contrail-scrape-ist:main",
        ]
    },
)