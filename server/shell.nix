# This is to initiate the default virtual environement
{ pkgs ? import <nixpkgs> {} }: 
pkgs.mkShell {

  nativeBuildInputs = with pkgs.buildPackages; [
    python3
      gcc-unwrapped
      ffmpeg
      wget
      libGL
      pkg-config
      python311Packages.flask
      python311Packages.cryptography
  ];

  LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib/:/run/opengl-driver/lib/";
# using pip here in case some packages are not available in 
# the nix store, e.g. tensorflow_hub, sklearn, etc.
    # 
  shellHook = ''
    echo "welcome to ur shell environement"
    python -m venv venv 
    source ./venv/bin/activate
    pip install paho-mqtt pyDH tensorflow tensorflow_hub tensorrt --upgrade
    mkdir ./venv/models
    test -f ./venv/models/metrabs_s_256/saved_model.pb && echo "model already installed!" || (
		    echo "loading the 'metrabs_s_256' model..." &&
        mkdir -p ./venv/models/metrabs_s_256 &&
		    wget --output-document ./venv/models/metrabs_s_256/3Dmodel https://bit.ly/metrabs_s_256 &&
		    tar xzf ./venv/models/metrabs_s_256/3Dmodel --directory ./venv/models/metrabs_s_256
		    )
    ./venv/bin/python main.py
    '';
}
