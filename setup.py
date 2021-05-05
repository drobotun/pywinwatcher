from setuptools import setup, find_packages
import subprocess
import sys

with open('README.rst', 'r', encoding='utf-8') as readme_file:
    readme = readme_file.read()
with open('HISTORY.rst', 'r', encoding='utf-8') as history_file:
    history = history_file.read()

def pip_install(package_name):
    subprocess.call(
        [sys.executable, '-m', 'pip', 'install', package_name]
    )

pip_install('wmi')

setup(
    name='pywinwatcher',
    version='0.0.1',
    description='Operating system event monitoring package',
    long_description=readme + '\n\n' + history,
    author='Evgeny Drobotun',
    author_email='drobotun@xakep.ru',
    url='https://github.com/drobotun/pywinwatcher',
    zip_safe=False,
    license='MIT',
    keywords='system event, monitoring, file system event, process event, registry event',
    project_urls={
        'Source': 'https://github.com/drobotun/pywinwatcher'
    },
    classifiers=[
        'Environment :: Win32 (MS Windows)',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: Microsoft :: Windows',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.8',
    ],
    packages=find_packages(),
    )
