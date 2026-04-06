{
  description = "lexemancy-site — pulse log generator dev environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        python = pkgs.python3.withPackages (ps: with ps; [
          requests
          pyyaml
          python-dotenv
          pytest
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [ python ];

          shellHook = ''
            export PYTHONPATH="${python}/${python.sitePackages}"
          '';
        };
      }
    );
}
