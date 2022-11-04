#!/usr/bin/env python3
import sys
import os
import json
import sqlite3
from sioyek.sioyek import Sioyek, Highlight, clean_path, DocumentPos

LOCAL_DATABASE_FILE = "/home/spike/.local/share/sioyek/local.db"
SHARED_DATABASE_FILE = "/home/spike/.local/share/sioyek/shared.db"
SIOYEK_PATH = "/usr/bin/sioyek"


def load_ko_export(filename):
    export = None
    with open(filename, 'r') as f:
        try:
            export = json.load(f)
        except Exception as e:
            raise e
    return export

def to_abs(doc, hi):
    begin, end = doc.get_text_selection_begin_and_end(hi['page'] - 1, hi['text'])
    if begin == (None, None) or end == (None,None):
        raise ValueError('highlight text not found')
    offset_x = (doc.page_widths[hi['page'] - 1]) / 2
    begin_pos = DocumentPos(hi['page'] -1, begin[0] - offset_x, begin[1])
    end_pos = DocumentPos(hi['page'] -1, end[0] - offset_x, end[1])
    return (doc.to_absolute(begin_pos), doc.to_absolute(end_pos))

def import_ko_highlight(book_export, sioyek, shared_db):
    book_title = ko_export.get('title')
    book_hash = ko_export.get('md5sum')
    path_hashes = sioyek.get_path_hash_map()
    hash_paths = {value: key for key, value in path_hashes.items()}
    local_book_path = hash_paths[book_hash]
    doc = sioyek.get_document(local_book_path)

    # filter highlight entries
    highlights = [entry for entry in book_export['entries'] if entry['sort'] == 'highlight']
    
    for hi in highlights:
        try:
            (hi['begin'],hi['end']) = to_abs(doc, hi)
            hi_type = 'k'
            insert_hi_shared_db(hi, book_hash ,shared_db)
        except ValueError as e:
            continue

    return


def insert_hi_shared_db(hi, hash, db):
    Q_HI_INSERT ="""
    INSERT INTO highlights (document_path,desc,type,begin_x,begin_y,end_x,end_y)
    VALUES ('{}','{}','{}',{},{},{},{});
    """.format(hash, hi['text'], "k", hi['begin'].offset_x, hi['begin'].offset_y, hi['end'].offset_x, hi['end'].offset_y)

    print(Q_HI_INSERT)
    db.execute(Q_HI_INSERT)
    db.execute('commit')

    return


if __name__ == "__main__":
    if len(sys.argv) < 2: 
        print("USAGE: {} KO_EXPORT.json ... \npass one book export per argument".format(sys.argv[0]))
        sys.exit(1)

    sioyek = Sioyek(SIOYEK_PATH, LOCAL_DATABASE_FILE, SHARED_DATABASE_FILE)
    shared_database = sqlite3.connect(clean_path(SHARED_DATABASE_FILE))

    for export in sys.argv[1:]:
        ko_export = load_ko_export(export)
        book_title = ko_export.get('title')

        if len(ko_export.get('entries')) > 0:
            print("importing entries from {}".format(book_title))
            import_ko_highlight(ko_export, sioyek, shared_database)
        else:
            print("file {} has no entries".format(book_title))

    shared_database.close()
    sioyek.close()

