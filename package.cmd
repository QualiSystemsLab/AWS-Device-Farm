cd ".\Environment\AWS Device Farm Server Driver"

"c:\Program Files\7-Zip\7z.exe" a -r "AWS Device Farm Server Driver.zip" *

move "AWS Device Farm Server Driver.zip" "..\AWS Shell\Resource Drivers - Python"

cd "..\AWS Shell"

del "AWS Shell.zip"

"c:\Program Files\7-Zip\7z.exe" a -r "AWS Shell.zip" *

cd ..\..