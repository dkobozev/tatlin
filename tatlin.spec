Name:           tatlin
Version:        0.3.0
Release:        1%{?dist}
Summary:        Lightweight G-code and STL viewer for 3D printing.

License:        GPL-2
URL:            https://dkobozev.github.io/tatlin/

Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools

Requires:       python3-wxpython4 python3-numpy python3-pyopengl python3-pillow python3-six mesa-libGLU

%description
Lightweight G-code and STL viewer for 3D printing.

%prep
%setup -q

%build
python3 setup.py build

%install
python3 setup.py install --skip-build --root $RPM_BUILD_ROOT
install -Dm644 tatlin.desktop %{buildroot}/usr/share/applications/tatlin.desktop
install -Dm644 tatlin/tatlin.png %{buildroot}/usr/share/icons/hicolor/64x64/apps/tatlin.png

%files
%{python3_sitelib}/tatlin/
%{python3_sitelib}/tatlin-*.egg-info/
/usr/bin/tatlin
/usr/share/applications/tatlin.desktop
/usr/share/icons/hicolor/64x64/apps/tatlin.png

%changelog
* Tue Oct 3 2023 Denis Kobozev <d.v.kobozev@gmail.com> - 0.3.0
- First RPM package build