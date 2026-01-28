{
  description = "OpenProject Sync Development Shell";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "aarch64-darwin";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python3
          python3Packages.requests
          python3Packages.python-dotenv
        ];

        shellHook = ''
          echo "OpenProject Sync Environment Loaded"
          echo "Run 'python sync.py' to upload roadmap."
        '';
      };
    };
}
