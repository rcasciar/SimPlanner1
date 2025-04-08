{pkgs}: {
  deps = [
    pkgs.freetype
    pkgs.pango
    pkgs.harfbuzz
    pkgs.glib
    pkgs.ghostscript
    pkgs.fontconfig
    pkgs.locale
    pkgs.glibcLocales
  ];
}
