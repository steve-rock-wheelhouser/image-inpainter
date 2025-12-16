%global debug_package %{nil}

Name:           image-inpainter
Version:    0.1.0
Release:    2
Summary:        Image inpainting application for removing objects from images.

License:        GPLv3
URL:            https://wheelhouser.com
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  desktop-file-utils
BuildRequires:  libappstream-glib
Requires:       hicolor-icon-theme
Requires:       gtk3

%description
Image Inpainter is a desktop application for removing unwanted objects from images using advanced AI techniques. It provides an easy-to-use interface for inpainting images.

%prep
%setup -q

%build
# Binary is already compiled

%install
rm -rf %{buildroot}

# Install binary to libexec (private directory)
install -d -m 755 %{buildroot}%{_libexecdir}/%{name}
install -m 755 image-inpainter.bin %{buildroot}%{_libexecdir}/%{name}/%{name}

# Install assets
cp -r assets %{buildroot}%{_libexecdir}/%{name}/

# Create wrapper script in /usr/bin
install -d -m 755 %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/%{name} <<EOF
#!/bin/bash
export GTK_THEME=Adwaita:dark
export QT_QPA_PLATFORMTHEME=gtk3
exec %{_libexecdir}/%{name}/%{name} "\$@"
EOF
chmod 755 %{buildroot}%{_bindir}/%{name}

# Install desktop file
install -d -m 755 %{buildroot}%{_datadir}/applications
desktop-file-install --dir=%{buildroot}%{_datadir}/applications com.wheelhouser.image_inpainter.desktop

# Install AppStream metadata
install -d -m 755 %{buildroot}%{_metainfodir}
install -m 644 com.wheelhouser.image_inpainter.metainfo.xml %{buildroot}%{_metainfodir}/

# Install Icon
install -d -m 755 %{buildroot}%{_datadir}/icons/hicolor/256x256/apps
install -m 644 assets/icons/icon.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/com.wheelhouser.image_inpainter.png
install -d -m 755 %{buildroot}%{_datadir}/icons/hicolor/scalable/apps
install -m 644 assets/icons/icon.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/com.wheelhouser.image_inpainter.svg

%files
%{_bindir}/%{name}
%{_libexecdir}/%{name}
%{_datadir}/applications/*.desktop
%{_metainfodir}/*.xml
%{_datadir}/icons/hicolor/*/apps/*.png
%{_datadir}/icons/hicolor/scalable/apps/*.svg
%license LICENSE

%post
touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

%postun
if [ $1 -eq 0 ] ; then
    touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi

%posttrans
gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%changelog
* Tue Dec 16 2025 Wheelhouser LLC <steve.rock@wheelhouser.com> - 0.1.0-2
- Automated build
* Tue Dec 16 2025 Wheelhouser LLC <steve.rock@wheelhouser.com> - 0.1.0-1
- Initial package

