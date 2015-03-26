import re
import string

from setuptools import setup


LINE_MATCH = re.compile(r'''
    ^(?P<version> .+?) \s*  # version number
    \((?P<date> [\d]{4}-[\d]{2}-[\d]{2}|\?\?\?\?-\?\?-\?\?)\)  # date
    \s* -- \s*  # formatting
    (?P<details> .+)$  # Release details
    ''', re.VERBOSE)


def versions(path='CHANGELOG.txt'):
    with open(path) as file:
        line = next(file).rstrip()
        while True:
            if line.startswith('#'):  # comment
                line = next(file).rstrip()
                continue
            elif not line:  # blank line
                line = next(file).rstrip()
                continue

            match = LINE_MATCH.search(line)
            if match is None:
                line = next(file).rstrip()
                continue  # unrecognised line

            version = {
                'version': match.group('version'),
                'date': match.group('date'),
                'desc': match.group('details'),
                'beta': False}

            details = []
            while True:
                line = next(file, None)
                if line is None:
                    break
                elif line.startswith(' '):
                    details.append(line.strip())
                elif not line.strip():
                    details.append('')
                else:
                    break
            version['changes'] = '\n'.join(details)

            if version['date'] == '????-??-??':
                version['version'] += 'b' + str(len(details))
                version['beta'] = True

            yield version
            if line is None:
                break


change_info = next(versions(), None)
if change_info is None:
    raise Exception("No available versions!")

version = change_info['version']
print("Processing version: " + version)
if change_info['beta']:
    print("NOTE!  THIS IS A BETA RELEASE!")

setup(
    name='ogitm',
    version=version,
    description='A OO-based Git Database',
    long_description=open('README.rst').read(),

    url='https://github.com/MrJohz/ogitm',
    author='Jonathan Frere',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',

        'Topic :: Database'
    ],

    keywords='git database',
    packages=['ogitm'],
    install_requires=list(open('requirements.txt')),
    extras_require={
        'dev': list(open('dev-requirements.txt')),
        'rtd': list(open('rtd-requirements.txt'))
    }
)
