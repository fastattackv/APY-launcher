# Documentation for the APY Update Language (AUL)
This documentation is for the version 2.0.0 of the AUL

## What is the AUL
This computer language is used to describe to the launcher what files have to be updated and how to update them.


## Commands documentation


### replacefile
The `replacefile` command is used to replace a file by its newer version.

It requires 1 argument: 
- `filepath`: the filepath of the file to replace. The path has to be in quotation marks to contain spaces. The updater downloads all the new files and replaces the specified ones.

Example of the command: `replacefile "dir/filepath.ext"`


### replacedir
The `replacedir` command is used to replace all files in a directory by their newer versions.

It requires 1 argument: 
- `path`: the path of the directory to replace. The path has to be in quotation marks to contain spaces. The directory is not replaced, only the files contained in it are. The updater downloads all the new files and replaces the specified ones.

Example of the command: `replacedir "dir/dir to replace"`


### createfile
The `createfile` command is used to create a file. If a file with the same name already exists, nothing happens.

It requires 1 argument: 
- `filepath`: the filepath to create the file to. The path has to be in quotation marks to contain spaces

Example of the command: `createfile "dir/filepath.ext"`


### createdir
The `createdir` command is used to create a directory. If a directory with the same name already exists, nothing happens.

It requires 1 argument: 
- `path`: the path to create the directory to. The path has to be in quotation marks to contain spaces

Example of the command: `createdir "dir/new dir"`


### deletefile
The `deletefile` command is used to delete a file. If there is no file at the given path, nothing happens.

It requires 1 argument: 
- `filepath`: the filepath of the file to delete. The path has to be in quotation marks to contain spaces

Example of the command: `deletefile "filepath.ext"`


### deletedir
The `deletedir` command is used to delete a directory. If there is no directory at the given path, nothing happens.

It requires 1 argument: 
- `path`: the filepath of the directory to delete. The path has to be in quotation marks to contain spaces

Example of the command: `deletedir dir`


### update
The `update` command is used to update a text a file without losing its content.

It requires at least 2 arguments: the filename and the way to modify it:
- `filepath`: the filepath to modify. The path has to be in quotation marks to contain spaces
- `modifier`: precises the way of modifying the file. It can be one of the following:
  - `newline`: adds a new empty line in the given file. Needs 1 argument:
    - The index where to add the line or `end` to add a line to the end of the file.
    - Ex: `update filename.ext newline index`
  - `deleteline`: removes a line in the given file. Needs 2 argument:
    - The way of deleting the line (`index` or `start`)
    - The index of the line to delete if `index` was selected or the string the line to delete starts with if `start` was selected.
    - Ex: `update filename.ext deleteline index line_index` or `update filename.ext deleteline start start_string`
  - `rewriteline`: replaces a line in the given file. Needs 3 argument:
    - The way of rewriting the line (`index` or `start`)
    - The index of the line to rewrite or `end` if `index` was selected or the string the line to rewrite starts with if `start` was selected
    - The new content of the line.
    - Ex: `update filename.ext rewriteline index line_index content` or `update filename.ext rewriteline start start_string content`
  - `modifyline`: splits the line at the given splitter_char and replaces the element at the given index by the given content. Needs 5 argument:
    - The way of modifying the line (`index` or `start`)
    - The index of the line to modify if `index` was selected or the string the line to modify starts with if `start` was selected
    - The character to split to. Should be a single character and not a string.
    - The index of the element to replace.
    - The content replacing the given element. The new content cannot contain spaces
    - Ex: `update filename.ext modifiyline index line_index splitter_char element_index new_content` or `update filename.ext modifiyline start start_string splitter_char element_index new_content`


### updatecsv
The `updatecsv` command is used to modify the `apps.csv` file.

It requires 4 arguments:
- The file to modify
- The type of app to modify (`game` / `bonus` / `config` / `folder` / `all`)
- The way of modifying the line (`add` / `delete` / `modify`)
- The index of the item to modify (index or `end`)
- A 5th argument if `modify` was selected: the new content of the modified items.
 
Example of the command: `updatecsv filename.ext all add end` or `updatecsv filename.ext game modify 3 new_content`
