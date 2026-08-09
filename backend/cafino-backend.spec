# PyInstaller spec for Cafino Local backend
from PyInstaller.utils.hooks import collect_all,collect_submodules
datas=[];binaries=[];hiddenimports=[]
for pkg in ['django','rest_framework','corsheaders','django_filters','drf_spectacular','rest_framework_simplejwt','whitenoise','cryptography','qrcode','pywebpush']:
    try:
        d,b,h=collect_all(pkg);datas+=d;binaries+=b;hiddenimports+=h
    except Exception:pass
hiddenimports+=collect_submodules('apps')+collect_submodules('config')
a=Analysis(['local_server.py'],pathex=['.'],binaries=binaries,datas=datas,hiddenimports=hiddenimports)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,a.binaries,a.datas,[],name='cafino-backend',console=False)
