from setuptools import setup, find_packages
from pathlib import Path

VERSION = '1.0.0'
DESCRIPTION = 'Product Tester Framework'
LONG_DESCRIPTION = 'Test Framework for HiL Testing'

frontend_dir = Path(__file__).parent / 'tester' / 'frontend'
files = [str(p.relative_to(Path(__file__).parent / 'tester')) for p in frontend_dir.rglob('*')]
files.append('Assets/*.*')

# Setting up
setup(
    name="tester",
    version=VERSION,
    url='git@github.com:yuvalmaran1/tester.git',
    author="Yuval Maran",
    author_email="yuvalmaran@gmail.com",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=[
        'plotly>=5.17.0',
        'dash>=2.14.0',
        'dash-bootstrap-components>=1.5.0',
        'Flask>=3.0.0',
        'Flask_SocketIO>=5.3.6',
        'numpy',
        'pyjson5>=1.6.4',
        'psycopg2-binary>=2.9.0'
    ],
    include_package_data=True,
    package_data={'': files}
)
