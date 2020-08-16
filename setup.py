import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

setup(
    name="contrail-scrape",
    version="0.1.2",
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
    package_dir={'': 'src'},
    packages=["ContrailScrape"],
    package_data = {'ContrailScrape': ['data/*.yaml']},
    install_requires=["beautifulsoup4", "tqdm==4.48.2", "lxml", \
        "PrettyTable", "html5lib",],
    entry_points={
        "console_scripts": [
            "contrail-scrape = ContrailScrape.main:main",
            "contrail-scrape-ist = ContrailScrape.scrape_ist:main",
        ]
    },
)