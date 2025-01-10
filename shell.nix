{
  pkgs ? import <nixpkgs> { },
}:

let
  name = "graph-et";
in
pkgs.mkShell ({
  name = "${name}-env";
  nativeBuildInputs = with pkgs; [
    python312
    black
    pyright
    taplo
    vscode-langservers-extracted
    zlib
    llvmPackages_19.libcxxClang
    zsh
  ];

  LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
    pkgs.stdenv.cc.cc
    pkgs.zlib
  ];

  shellHook = ''
    BLUE='\033[0;34m'
    NC='\033[0m'
    export SHELL=$(which zsh)
    export VENV_DIR="$(pwd)/.venv"

    if [ ! -d "$VENV_DIR" ]; then
      python3 -m venv "$VENV_DIR"
      source "$VENV_DIR/bin/activate"
      pip install --upgrade pip --quiet
      pip install -r requirements.txt --quiet
      pip install ipykernel jupyter build --quiet
    else
      source "$VENV_DIR/bin/activate"
    fi

    echo -e "${name} nix-shell activated: ''\${BLUE}$(which python3)''\${NC}"
    exec $SHELL
  '';
})
