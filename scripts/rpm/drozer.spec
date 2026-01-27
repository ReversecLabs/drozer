%define name 	drozer
%define version	%(git describe --tags  | cut -c 1-5)

%define _binaries_in_noarch_packages_terminate_build 0
%define _unpackaged_files_terminate_build 0
%define _missing_doc_files_terminate_build 0

# Don't try fancy stuff like debuginfo, which is useless on binary-only
# packages. Don't strip binary too
# Be sure buildpolicy set to do nothing
%define        __spec_install_post %{nil}
%define          debug_package %{nil}
%define        __os_install_post %{_dbpath}/brp-compress

Summary:	The Leading Security Testing The Leading Security Testing Framework for Android.
Name:		%{name}
Version:	%{version}
Release:	1
# For a breakdown of the licensing, see PACKAGE-LICENSING
License:	BSD and GPL2+ and Apache2 and MITx11
Group:		Reversec
URL:		https://labs.reversec.com
Source:		%{name}-%{version}.tar.gz
Requires:	python >= 2.7
Requires:	protobuf-python >= 2.4.1
Requires:	pyOpenSSL >= 0.12-1
Requires:	python-twisted-web >= 10.0.2

Requires: glibc(%{__isa_name}-32)
Requires: zlib(%{__isa_name}-32)
Requires: libstdc++(%{__isa_name}-32)

BuildArch:	noarch
AutoReq:	0

%description
drozer enables you to search for security vulnerabilities in apps and devices by assuming the role of an app and interacting with the Dalvik VM, other apps’ IPC endpoints and the underlying OS.
drozer provides tools to help you use and share public Android exploits. It helps you to deploy a drozer agent by using weasel – Reversec’s advanced exploitation payload.
For the latest Mercury updates, follow @reversec.
Features
drozer allows you to use dynamic analysis during an Android security assessment. By assuming the role of an Android app you can:
*find information about installed packages.
*interact with the 4 IPC endpoints – activities, broadcast receivers, content providers and services.
*use a proper shell to play with the underlying Linux OS (from the content of an unprivileged application).
*check an app’s attack surface, and search for known vulnerabilities.
*create new modules to share your latest findings on Android.
drozer’s remote exploitation features provide a unified framework for sharing Android payloads and exploits. It helps to reduce the time needed for vulnerability assessments and mobile red-teaming exercises, and includes the outcome of some of Reversec’s cutting-edge research into advanced Android payloads and exploits.
How it Works
drozer does all of this over the network: it does not require ADB.

%prep
%setup
%build
%install

rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT
cp -pa * %{buildroot}

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%{_bindir}/*
/etc/bash_completion.d/drozer
/usr/lib/python2.7/dist-packages/*
%{_defaultdocdir}/%{name}
