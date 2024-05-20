# This is to initiate the default virtual environement
{ pkgs ? import <nixpkgs> {} }: 
pkgs.mkShell {

  nativeBuildInputs = with pkgs.buildPackages; [
    python3
      ffmpeg
      wget
      tar
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

    test -f ./venv/models/movenet/thunder/saved_model.pb &&
    test -d ./venv/models/movenet/thunder/variables/ &&
    echo "The 'Movenet thunder' model already installed!" || (
        echo "loading Movenet thunder..." &&
        wget --output-document ./venv/models/movenet/thunder/out.tar.gz
        https://www.kaggle.com/api/v1/models/google/movenet/tensorFlow2/singlepose-thunder/4/download &&
        tar xzf ./venv/models/movenet/thunder/out.tar.gz --directory ./venv/models/movenet/thunder/
        )

    pip install 'keras==2.15' pyDH 'tensorflow==2.15' tensorflow_hub --upgrade
    source ./venv/bin/activate
    '';
}
