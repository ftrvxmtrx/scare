with import <nixpkgs> {};
stdenv.mkDerivation {
 name = "scare";
 buildInputs = with python3Packages; [
  capstone
  keystone-engine
  numexpr
  unicorn
 ];
}
