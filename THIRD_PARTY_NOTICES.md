# Third-party material policy

ELF600 is a commercial product of Science Solutions International Laboratory.
Its manuals, help pages, wiki text, example files, Python wrappers,
configuration files, error tables, binaries, and solver outputs are not
licensed under this repository's BSD-3-Clause license and are not bundled in
the source distribution or wheel.

Links and product names are provided only for identification. The summaries,
schemas, MCP Resources, validation contracts, and public sample decks shipped
by this repository are maintained as repository-owned material. Users must
obtain the product and its documentation from the vendor under the applicable
terms.

The optional runtime adapter discovers a user-installed MAGIC/ELFIN DLL and
calls a fixed API subset through Python `ctypes`. The DLL remains on the user's
machine and is neither copied into nor linked as part of this distribution.
