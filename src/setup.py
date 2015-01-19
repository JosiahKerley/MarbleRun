from setuptools import setup

setup(name='marblerun',
      version='0.1',
      description='A simple batch processor',
      url='http://github.com/JosiahKerley/MarbleRun',
      author='Josiah Kerley',
      author_email='josiahkerley@gmail.com',
      license='MIT',
      packages=['marblerun'],
      zip_safe=False
	  install_requires=['redis'],)