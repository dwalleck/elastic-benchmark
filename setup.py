from setuptools import setup, find_packages

setup(
    name='elastic-benchmark',
    version='0.0.1',
    description='Parses a given input and inserts into ElasticSearch.',
    author='Stephen Lowrie, Daryl Walleck',
    author_email='stephen.lowrie@rackspace.com',
    url='https://github.com/arithx/elastic-benchmark',
    packages=find_packages(),
    install_requires=open('requirements.txt').read(),
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: Other/Proprietary License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ),
    entry_points={
        'console_scripts': [
            'elastic-benchmark = elastic_benchmark.parse_results:entry_point']})