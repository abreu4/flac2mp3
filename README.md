flac2mp3
----

`flac2mp3` is a Python wrapper around several tools used for encoding FLAC and
MP3 files, namely `flac`, `metaflac`, and `lame` (all of which it assumes are
installed). It uses multiple cores to simultaneously re-encode FLAC files as MP3
files while preserving any id3 tags found.

Supported Platforms
----
`flac2mp3` has been tested on Snow Leopard and Ubuntu Linux, but should work on
any environment that interfaces with Python's `subprocess` module and exposes
the required programs to the script.

How it Works
----
The utility walks the given files and/or directories and collects all the FLAC
files it finds, then passes them through `flac` to decode them, piping the
output through `lame` to re-encode them, and stores them in the output directory
intelligently using the nearest common ancestor directory as a template to
ensure they don't end up lumped illogically in the output directory.

Simple Usage
----
`python flac2mp3.py [-i INPUT_DIR]`

Creates an `MP3/` directory inside the input folder, where it saves copies of all the converted FLAC files as `.mp3` files.

Shortcomings
----
Currently, there's no way to set the `lame` encoding options from the command
line, and they're hardcoded to `-m s --vbr-new -V2`. To change them, edit the
`lame_args` list in the `transcode` method.
