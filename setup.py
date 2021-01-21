import pathlib
import os, shutil
from setuptools import setup

# The directory containing this file
HERE = str(pathlib.Path(__file__).parent)
HOME = os.environ['HOME']

# The text of the README file
README_FILE= HERE+'/README.md'
README = open(README_FILE).read()

#copy over the config file to HOME/contrail-scrape
if not os.path.isdir(HOME+'/contrail-scrape'):
    os.mkdir(HOME+'/contrail-scrape')
if os.path.isdir(HOME+'/contrail-scrape'):
    shutil.copy(HERE+'/src/ContrailScrape/data/hosts.yaml', HOME+'/contrail-scrape')

setup(
    name="contrail-scrape",
    version="0.1.13",
    description="crawler for all the APIs of Juniper Contrail nodes",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/aniruddhamonker/contrail-scrape",
    author="Aniruddh Amonker",
    author_email="aamonker@juniper.net",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.8"
    ],
    package_dir={'': 'src'},
    packages=["ContrailScrape"],
    package_data = {'ContrailScrape': ['data/*.yaml']},
    install_requires=["beautifulsoup4", "tqdm==4.48.2", "PrettyTable==0.7.2"\
        , "lxml", "html5lib", 'requests >= 2.9.1', 'PyYAML'],
    entry_points={
        "console_scripts": [
            "contrail-scrape = ContrailScrape.main:main",
            "contrail-scrape-ist = ContrailScrape.scrape_ist:main",
        ]
    },
)