from setuptools import setup, find_packages

required = [
    'requests>=2.5.1'
]

setup(
    name='buildapi_client',
    version='0.6.3.dev0',
    packages=find_packages(),

    install_requires=required + ['pytest-runner'],
    tests_require=required + ['mock', 'pytest'],

    # Meta-data for upload to PyPI
    author='Armen Zambrano G.',
    author_email='armenzg@mozilla.com',
    description="Package designed to trigger jobs through Release Engineering's "
                "buildapi self-serve service.",
    license='MPL2',
    url='https://github.com/armenzg/buildapi_client',
)
