%define		plugin	check_json_health
Summary:	Nagios plugin to check JSON health endpoints
Name:		nagios-plugin-%{plugin}
Version:	1.0
Release:	2
License:	Public Domain (CC0 1.0)
Group:		Networking
Source0:	%{plugin}.py
Source1:	%{plugin}.cfg
URL:		https://github.com/pld-linux
Requires:	python3
Requires:	python3-modules
BuildArch:	noarch
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		_sysconfdir	/etc/nagios/plugins
%define		plugindir	%{_prefix}/lib/nagios/plugins

%description
Generic Nagios plugin for checking HTTP(S) endpoints that return JSON
with standard health fields (exit_code, status, message). The server
owns all threshold logic; the plugin simply fetches, extracts, and
forwards the status to Nagios.

%prep
%setup -q -c -T
cp -p %{SOURCE0} %{plugin}

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_sysconfdir},%{plugindir}}
install -p %{plugin} $RPM_BUILD_ROOT%{plugindir}/%{plugin}
cp -p %{SOURCE1} $RPM_BUILD_ROOT%{_sysconfdir}/%{plugin}.cfg

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(644,root,root,755)
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/%{plugin}.cfg
%attr(755,root,root) %{plugindir}/%{plugin}
