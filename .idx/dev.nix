{ pkgs, ... }: {
  # Which nixpkgs channel to use.
  channel = "stable-23.11"; # or "unstable"

  # Use https://search.nixos.org/packages to find packages
  packages = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.black
  ];

  # Sets environment variables in the workspace
  env = {};

  idx = {
    # Use "publisher.id" from https://open-vsx.org/ to list general extensions
    extensions = [
      # "ms-python.python@2024.6.0"
      "esbenp.prettier-vscode"
    ];

    # Enable previews
    previews = {
      enable = true;
    };

    # Workspace lifecycle hooks
    workspace = {
      # Runs when a workspace is first created
      onCreate = {
        # No specific setup on create
      };

      # Runs when the workspace is (re)started
      onStart = {
        # Create and activate a Python virtual environment
        venv_and_source = "python3 -m venv .venv; source .venv/bin/activate";

        install_ms-python_extension = "wget https://open-vsx.org/api/ms-python/python/2024.12.3/file/ms-python.python-2024.12.3.vsix; code --force --install-extension *.vsix; rm *.vsix";
      };
    };
  };
}