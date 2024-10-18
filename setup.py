from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

requirements.append('gmx_python_sdk @ git+https://github.com/50shadesofgwei/gmx_python_sdk_custom.git@main')

setup(
    name='perpsQuoter',
    version='0.0.1',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            
        ],
    },
    description='compare quotes for perps positions',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='zk50.eth',
    url='https://github.com/50shadesofgwei/',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ]
)