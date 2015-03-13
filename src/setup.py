# -*- coding: cp949 -*-
# vim: et ts=9 sts=4 sw=4
# python setup.py py2exe

from distutils.core import setup
#from myADO import *
import py2exe

setup(
    name="preparedsql",
    zipfile=None,
    windows=[{"script":"preparedsql.pyw", 
            "icon_resources":[(1,"kkt.ico")]}],
    options={"py2exe":{"compressed":1, "optimize":2, "dll_excludes":["MSVCP90.dll"]}}
)
