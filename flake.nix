{
  description = "A very basic flake";

  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = nixpkgs.legacyPackages.${system};
    in {
      devShell = pkgs.mkShell {
        nativeBuildInputs = with pkgs; [
          (python3.withPackages (p: [
            p.pygobject3
            p.python-language-server
            p.mpd2
            p.i3ipc
          ]))
          gobject-introspection
          gtk3
          gtk-layer-shell
          libappindicator
        ];
      };
    });
}
