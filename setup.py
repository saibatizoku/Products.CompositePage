import os
from setuptools import setup
from setuptools import find_packages

NAME = 'CompositePage'

here = os.path.abspath(os.path.dirname(__file__))
package = os.path.join(here, 'Products', NAME)

def _package_doc(name):
    f = open(os.path.join(package, name))
    return f.read()

_boundary = '\n' + ('-' * 60) + '\n\n'
README = ( _package_doc('README.txt')
         + _boundary 
         + _package_doc('CHANGES.txt')
         )

setup(name='Products.%s' % NAME,
      version=_package_doc('version.txt').strip(),
      description='%s product' % NAME,
      long_description=README,
      classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "Framework :: Zope2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Zope Public License",
        "Programming Language :: Python",
        "Topic :: Software Development",
        ],
      keywords='web application server zope zope2 cmf plone',
      author="Shane Hathaway",
      author_email="shane@hathawaymix.org",
      url="http://pypi.python.org/pypi/Products.%s" % NAME,
      license="ZPL 2.1 (http://www.zope.org/Resources/License/ZPL-2.1)",
      packages=find_packages(),
      include_package_data=True,
      namespace_packages=['Products'],
      zip_safe=False,
      install_requires=['setuptools',
                       ],
      tests_require=[],
      test_suite="Products.%s.tests" % NAME,
      entry_points="""
      """,
      )
