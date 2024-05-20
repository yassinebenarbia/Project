# This is to initiate the default virtual environement
{ pkgs ? import <nixpkgs> {} }: 
pkgs.mkShell {

  nativeBuildInputs = with pkgs.buildPackages; [
    python3
      ffmpeg
      wget
      pkg-config
      musl
      hdf5
      glibc
      glib
      python311Packages.flask
      python311Packages.cryptography
      python311Packages.paho-mqtt
      python311Packages.h5py
  ];

  LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib/:/run/opengl-driver/lib/";
# using pip here in case some packages are not available in 
# the nix store, e.g. tensorflow_hub, sklearn, etc
  shellHook = ''
    echo "welcome to ur shell environement"
    python -m venv venv 
    source ./venv/bin/activate
    pip install tensorflow tensorflow_hub pyDH
    '';
}
