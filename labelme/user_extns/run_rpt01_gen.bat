@echo off
setlocal EnableExtensions DisableDelayedExpansion

net use m:
if errorlevel 1 (
net use m: "\\ussomgensvm00.allergan.com\lifecell\Depts\Tissue Services\Tmp"
)
set IMGROOT=m:\MSA\Annot\Ground Truth
set LOGDIR=m:\MSA\Logs
set CFGDIR=m:\MSA\Cfg
set envuser=MHERZO

rem --------------------------------------- 
rem Set up condarc if needed
rem ---------------------------------------
set curuser=%username%
set targfile=%userprofile%\.condarc
set srcfile=m:\MSA\Cfg\default_condarc

if /i %curuser% == %envuser% goto use_env_rc
if not exist %targfile% (
	echo Copy %srcfile% %targfile% 
	Copy %srcfile% %targfile% 
) else ( 
	echo Using condarc %targfile% to reference environment in %envuser% 
	)
goto endcopy

:use_env_rc
echo User %curuser% -- using condarc %targfile% >> "%LOGFILE%" 2>&1

:endcopy
echo End finding/setting up condarc

call C:\ProgramData\Anaconda3\condabin\activate.bat GUIAutomation 

m:
cd "m:\MSA\Util\export_images"

echo Running python gen_report.py
call python gen_report.py

:EndStartup
echo Process ends.  Return code=%ERRORLEVEL% 

endlocal