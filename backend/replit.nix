{ pkgs }:
{
  deps = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.postgresql
    pkgs.libpq
    pkgs.gcc
    pkgs.openssl
  ];
  env = {
    LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.libpq
      pkgs.openssl
      pkgs.stdenv.cc.cc.lib
    ];
    PYTHONPATH = "${pkgs.python311}/lib/python3.11/site-packages";
  };
}
