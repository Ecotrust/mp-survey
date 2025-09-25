from setuptools import setup, find_packages

setup(
    name='survey',
    version='0.0.1',
    description='Survey module for Madrona Platform',
    author='Your Name',
    author_email='ksdev@ecotrust.org',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Django>=3.2',
    ],
    classifiers=[
        'Framework :: Django',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
)