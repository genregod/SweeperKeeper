{pkgs}: {
  deps = [
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
