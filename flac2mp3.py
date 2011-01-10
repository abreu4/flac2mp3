#!/usr/bin/env python

import os
import re
import tempfile
import subprocess as sp
import multiprocessing as mp

def transcode(infile):
    """
    Transcodes a single flac file into a single mp3 file.  Preserves the file
    name but changes the extension.  Copies flac tag info from the transcoded
    file to the new file.
    """

    # get the decoded flac data from the given file using 'flac', saving it to a
    # string.
    flac_args = ["flac", "--silent", "-c", "-d", infile]
    p_flac = sp.Popen(flac_args, stdout=sp.PIPE)
    flac_data = p_flac.communicate()[0]

    # write the decoded flac data to a temporary file, saving the file name for
    # use later with 'lame'
    flacdata_filename = None
    with tempfile.NamedTemporaryFile(prefix="flacdata_", delete=False) as f:
        flacdata_filename = f.name
        f.write(flac_data)

    # get a new file name for the mp3 based on the input file's name
    mp3_filename = get_changed_file_ext(infile, ".mp3")

    # get the tags from the input file
    flac_tags = get_tags(infile)

    # arguments for 'lame', including bitrate and tag values
    bitrate = 320
    lame_args = ["lame", "-h", "-m", "s", "--cbr", "-b", str(bitrate),
            "--add-id3v2", "--silent",
            "--tt", flac_tags["TITLE"],
            "--ta", flac_tags["ARTIST"],
            "--tl", flac_tags["ALBUM"],
            "--ty", flac_tags["DATE"],
            "--tc", flac_tags["COMMENT"],
            "--tn", flac_tags["TRACKNUMBER"] + "\\" + flac_tags["TRACKTOTAL"],
            "--tg", flac_tags["GENRE"],
            flacdata_filename, mp3_filename]

    # encode the file using 'lame' and wait for it to finish
    p_lame = sp.Popen(lame_args)
    p_lame.wait()

    # remove the temporary data file
    os.remove(flacdata_filename)

    print "Finished transcoding '%s' to '%s'." % (infile, mp3_filename)

def get_changed_file_ext(fname, ext):
    """
    Transforms the given filename's extension to the given extension.  'ext' is
    the new extension, 'fname' is the file name transformation is to be done on.
    """

    # determine the new file name (old file name minus the extension if it had
    # one, otherwise just the old file name with new extension added).
    new_fname = fname

    # if we have a file extension, strip the final one and get the base name
    if len(fname.rsplit(".", 1)) == 2:
        new_fname = fname.rsplit(".", 1)[0]

    # add the new extension
    new_fname += ext

    return new_fname

def get_tags(infile):
    """
    Gets the flac tags from the given file and returns them as a dict.  Ensures
    a minimun set of id3v2 tags is available, giving them default values if
    these tags aren't found in the orininal file.
    """

    # get tag info text using 'metaflac'
    metaflac_args = ["metaflac", "--list", "--block-type=VORBIS_COMMENT", infile]
    p_metaflac = sp.Popen(metaflac_args, stdout=sp.PIPE)
    metaflac_text = p_metaflac.communicate()[0]

    # matches all lines like 'comment[0]: TITLE=Misery' and extracts them to
    # tuples like ('TITLE', 'Misery'), then stores them in a dict.
    pattern = "\s+comment\[\d+\]:\s+([^=]+)=([^\n]+)\n"

    # get the comment data from the obtained text
    tag_dict = {}
    for t in re.findall(pattern, metaflac_text):
        tag_dict[t[0]] = t[1]

    # ensure all possible id3v2 tags are present, giving them default values if
    # not.
    if "TITLE" not in tag_dict:
        tag_dict["TITLE"] = "NONE"
    if "ARTIST" not in tag_dict:
        tag_dict["ARTIST"] = "NONE"
    if "ALBUM" not in tag_dict:
        tag_dict["ALBUM"] = "NONE"
    if "DATE" not in tag_dict:
        tag_dict["DATE"] = "1"
    if "COMMENT" not in tag_dict:
        tag_dict["COMMENT"] = ""
    if "TRACKNUMBER" not in tag_dict:
        tag_dict["TRACKNUMBER"] = "00"
    if "TRACKTOTAL" not in tag_dict:
        tag_dict["TRACKTOTAL"] = "00"

    return tag_dict

def walk_dir(d, follow_links=False):
    """
    Returns all the file names in a given directory, including those in
    subdirectories.  if 'follow_links' is True, symbolic links will be followed.
    This option can lead to infinite looping since the function doesn't keep
    track of which directories have been visited.
    """

    # attempt to get the files in the given directory, returning an empty list
    # if it failed.
    contents = []
    try:
        contents = os.listdir(d)
        
        # add original directory name to every listed file
        contents = map(lambda x: os.path.join(d, x), contents)
    except OSError:
        return []

    # normalize all returned file names
    contents = map(os.path.abspath, contents)

    # add all file names to a list recursively
    new_files = []
    for f in contents:
        # skip links if specified
        if not follow_links and os.path.islink(f):
            pass

        # add all the files under a dir to the list
        if os.path.isdir(f):
            new_files.extend(walk_dir(f, follow_links=follow_links))
        # add files to the list
        else:
            new_files.append(f)

    return new_files

if __name__ == "__main__":
    import sys

    # get the number of threads we should use while transcoding (usually twice
    # the number of processors, or 2 if that number can't be determined).
    thread_count = 2
    try:
        thread_count = 2 * mp.cpu_count()
    except NotImplementedError:
        pass
    
    # find all the flac files in the given directory
    args = sys.argv
    flacfiles = filter(lambda x: x.lower().endswith(".flac"), walk_dir(args[1]))

    # transcode all the found files
    pool = mp.Pool(processes=thread_count)
    result = pool.map_async(transcode, flacfiles)
    result.get()