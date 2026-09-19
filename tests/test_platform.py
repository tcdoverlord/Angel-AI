from pathlib import Path
from angel_platform.core import Kernel
from angel_platform.builder import build_zip
from zipfile import ZipFile

def test_kernel_modules():
    k=Kernel(); assert len(k.modules)>=6; assert any(m.name=='Windows Hardening Toolkit' for m in k.modules)

def test_module_match():
    k=Kernel(); assert k.find_modules('scan modules')

def test_build_zip(tmp_path):
    src=tmp_path/'src'; src.mkdir(); (src/'hello.txt').write_text('hello')
    out=tmp_path/'out.zip'; build_zip(src,out); assert out.exists()
    with ZipFile(out) as z: assert 'hello.txt' in z.namelist(); assert 'BUILD_MANIFEST.json' in z.namelist()
