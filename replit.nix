{pkgs}: {
  deps = [
    pkgs.libev
    pkgs.python-launcher
    pkgs.geckodriver
    pkgs.rustc
    pkgs.pkg-config
    pkgs.libxcrypt
    pkgs.libiconv
    pkgs.cargo
    pkgs.openssl
    pkgs.postgresql
  ];
}
